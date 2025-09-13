import ast
import json
import frappe
from datetime import datetime, time, timedelta
from .reccurring_event import generate_recurrences
from frappe.utils import add_to_date, now_datetime


try:
    settings_doc = frappe.get_doc("Checklist Settings")
    maximum_task_limit = settings_doc.maximum_task_limit
    if_task_on_holiday__it_should_created_on__ = settings_doc.if_task_on_holiday__it_should_created_on__
    holiday_calendar = settings_doc.holiday_calendar
except Exception as e:
    print("Exception: ", str(e))

def calculate_child_occurence():
    """Calculate next execution time based on frequency."""
    now = now_datetime()
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)  # Monday
    end_of_week = (start_of_week + timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)  # Sunday

    frequency_map = {
        "Start Of Month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        "End Of Month": add_to_date(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), months=1, days=-1),
        "Start Of Quarter": datetime(now.year, (now.month - 1) // 3 * 3 + 1, 1).replace(hour=0, minute=0, second=0, microsecond=0),
        "End Of Quarter": add_to_date(datetime(now.year, (now.month - 1) // 3 * 3 + 1, 1).replace(hour=0, minute=0, second=0, microsecond=0), months=3, days=-1),
        "Start Of Half Yearly": datetime(now.year, 1 if now.month <= 6 else 7, 1).replace(hour=0, minute=0, second=0, microsecond=0),
        "End Of Half Yearly": datetime(now.year, 6 if now.month <= 6 else 12, 30).replace(hour=0, minute=0, second=0, microsecond=0),
        "Start Of Week": start_of_week,
        "End Of Week": end_of_week,
    }
    return frequency_map


def schedule_tasks():
    # Get all tasks that need to be scheduled today at midnight
    try:
        tasks_to_schedule = frappe.get_all('Master Tasks', fields=['*'], filters={'active': 1})
        for task_doc in tasks_to_schedule:
            task_data = {
                "name": task_doc.name,
                "task_type": task_doc.task_type,
                "subject": task_doc.subject,
                "frequency": task_doc.task_frequency,
                "occurrence": int(task_doc.task_occurence),
                "time_sensitive": task_doc.time_sensitive,
                "interval": task_doc.intervals,
                "time_interval": task_doc.interval if task_doc.intervals else None,
                "time_units": task_doc.time_units if task_doc.intervals else None,
                "time": task_doc.add_time if task_doc.time_sensitive else None,
                "child_occurrence": task_doc.occurence if task_doc.time_sensitive else None,
                "start_date": task_doc.start_date,
                "end_date": task_doc.end_date,
                "repeat_days": ast.literal_eval(task_doc.repeat_days or "[]"),  # Ensure it's a list
                "monthly_repeat_type": task_doc.month_repeat_type,
                "yearly_repeat_type": task_doc.year_repeat_type,
                "repeat_interval": task_doc.repeat_interval,
                "interval_unit": task_doc.interval_unit,
                "details": task_doc.details,
                "attachments": task_doc.attachments,
                "from_time": task_doc.from_time,
                "to_time": task_doc.to_time,
                "project_name": "Checklist OneTime" if task_doc.task_type == "One-Time" else "Checklist Recurring",
                "allocate_on_holiday": task_doc.allocate_on_holiday,
                "task_assigner": task_doc.task_assigner
            }
            employees = frappe.get_all("Master Task Assignees", filters={"parent": task_doc.name}, fields=["employee"])
            if not employees:
                print(f"No employees found for task {task_doc.name}.")
                continue
            if task_data["task_type"] == "Recurring":
                dates = generate_recurrences(
                    start_datetime= datetime.strptime(str(task_data["start_date"]), "%Y-%m-%d"),
                    recurrence_type=task_data["interval_unit"].lower(),
                    interval=int(task_data["repeat_interval"]),
                    weekdays=task_data["repeat_days"],
                    count=maximum_task_limit,
                    data=task_data["monthly_repeat_type"] if task_data["interval_unit"] == "month" else task_data["yearly_repeat_type"],
                    until= datetime.strptime(str(task_data["end_date"]), "%Y-%m-%d") if task_data["end_date"] else None
                ) 

            else:
                # For non-recurring tasks, use the start date
                dates = []
            for employee in employees:
                user = employee['employee']
                employee = frappe.get_value("Employee", {"user_id": user}, "name")
                if not employee:
                    print(f"Employee not found for user {user}. Skipping task assignment.")
                    continue
                if frappe.db.has_column("Employee", "default_shift"):
                    default_shift = frappe.db.get_value("Employee", employee, "default_shift", cache=True)
                else:
                    default_shift = None
                employee_data = {
                    "employee": employee,
                    "shift": default_shift,
                    "department": frappe.db.get_value("Employee", employee, "department", cache=True),
                }

                # Set shift start and end, use defaults if not set or shift is missing
                default_shift_start = "09:00:00"  # 09:00 AM
                default_shift_end = "18:00:00"    # 06:00 PM

                if employee_data["shift"]:
                    shift_doc = frappe.get_doc("Shift Type", employee_data["shift"])
                    employee_data["shift_start"] = str(getattr(shift_doc, "start_time", None) or default_shift_start)
                    employee_data["shift_end"] = str(getattr(shift_doc, "end_time", None) or default_shift_end)
                else:
                    print(f"Warning: No default shift assigned for employee {employee}. Using default shift times.")
                    employee_data["shift_start"] = default_shift_start
                    employee_data["shift_end"] = default_shift_end

                print(type(employee_data["shift_start"]), type(employee_data["shift_end"]))

                shift_start_time = string_to_time(employee_data["shift_start"])
                shift_end_time = string_to_time(employee_data["shift_end"])

                # Ensure shift times are valid
                if shift_start_time >= shift_end_time:
                    raise ValueError("Employee shift start time must be earlier than the end time.")
                
                if task_data["task_type"] == "Recurring":
                    print(f"Processing recurring task for employee {employee} with start date {task_data['start_date']}")
                    # Pass the task and employee data as dictionaries to the function
                    for date in dates:
                        # If a holiday calender exists and tasks need not to be assigned on holidays
                        print("checking holiday calender and if allocation on holiday")
                        if holiday_calendar and task_data["allocate_on_holiday"] == 0:
                            print("holiday calendr available and allocation on holiday false")
                            holiday_list_doc_name = frappe.get_value(
                                "Holiday List",
                                {
                                    "from_date": ["<=", task_data[start_date]],
                                    "to_date": [">=", task_data[start_date]],
                                    },          "name",
                                )
                            holiday_list_doc = frappe.get_doc("Holiday List", holiday_list_doc_name)
                            is_date_on_holiday = frappe.db.exists(
                                    "Holiday",
                                    {
                                        "parent": holiday_list_doc_name,
                                        "parenttype": "Holiday List",
                                        "holiday_date": date
                                    })
                            if is_date_on_holiday not in ['', None]:
                                is_date_on_holiday = True
                            else:
                                is_date_on_holiday = False
                            while is_date_on_holiday:
                                if if_task_on_holiday__it_should_created_on__ == 'After':
                                    date = date + timedelta(days=1)
                                    is_date_on_holiday = frappe.db.exists(
                                    "Holiday",
                                    {
                                        "parent": holiday_list_doc_name,
                                        "parenttype": "Holiday List",
                                        "holiday_date": date
                                    })
                                    if is_date_on_holiday not in ['', None]:
                                        is_date_on_holiday = True
                                    else:
                                        is_date_on_holiday = False
                                elif if_task_on_holiday__it_should_created_on__ == 'Before':
                                    date = date - timedelta(days=1)
                                    is_date_on_holiday = frappe.db.exists(
                                    "Holiday",
                                    {
                                        "parent": holiday_list_doc_name,
                                        "parenttype": "Holiday List",
                                        "holiday_date": date
                                    })
                                    if is_date_on_holiday not in ['', None]:
                                        is_date_on_holiday = True
                                    else:
                                        is_date_on_holiday = False
                            
                        # Create the task for the current iteration
                        start_time = calculate_start_time(
                            shift_start_time, date
                        )
                        end_time = calculate_end_time(
                            shift_end_time, start_time, date
                        )
                        print(f"Start time: {start_time}, End time: {end_time}")
                        create_task_for_employee(task_data, start_time, end_time, user)
                        task_doc = frappe.get_doc("Master Tasks", task_doc.name)
                        watchers = [watcher.user for watcher in task_doc.watchers if watcher.email_sent == 0]
                        if watchers:
                            send_recurring_watcher_email(task_data, watchers)
                            for watcher in task_doc.watchers:
                                watcher.email_sent = 1
                            task_doc.save()
                else:
                    print(f"Processing non-recurring task for employee {employee} with start date {task_data['start_date']}")
                    # For non-recurring tasks, use the start date directly
                    start_date = task_data["start_date"]
                    end_date = task_data["end_date"] if task_data["end_date"] else start_date

                    start_time = task_data["from_time"] or shift_start_time
                    end_time = task_data["to_time"] or shift_end_time

                    start_time = calculate_start_time(
                        start_time, start_date
                    )
                    end_time = calculate_end_time(
                        end_time, start_time, end_date
                    )
                    print(f"Start time: {start_time}, End time: {end_time}")
                    create_task_for_employee(task_data, start_time, end_time, user)
                    task_doc = frappe.get_doc("Master Tasks", task_doc.name)
                    watchers = [watcher.user for watcher in task_doc.watchers if watcher.email_sent == 0]
                    if watchers:
                        send_one_time_task_mail(task_data, watchers)
                        for watcher in task_doc.watchers:
                            watcher.email_sent = 1
                        task_doc.save()
    except Exception as e:
        print(f"Error scheduling tasks: {str(e)}")
        frappe.log_error(f"Error scheduling tasks: {str(e)}")

def calculate_start_time(shift_start, date):
    try:
        start_time = datetime.combine(date, time.fromisoformat(str(shift_start)))
        return start_time
    except Exception as e:
        print(f"Error calculating start time: {str(e)}")
        raise ValueError("Failed to calculate start time.")

def calculate_end_time(shift_end, start_time, date):
    try:
        end_time = datetime.combine(date, time.fromisoformat(str(shift_end)))
        return end_time
    except Exception as e:
        print(f"Error calculating end time: {str(e)}")
        raise ValueError("Failed to calculate end time.")

def create_task_for_employee(task_data, start_time, end_time, employee):
    """Create the task and assign it to the employee if it doesn't already exist."""
    try:
        user = employee
        emp = frappe.get_value("Employee", {"user_id": user}, "name")

        print(f"Creating task for employee {user} with start_time {start_time} and end_time {end_time}.")
        # Check if a task already exists for the given start_time and due_date
        existing_task = frappe.get_all(
            'Task',
            filters={
                'custom_master_task': task_data["name"],
                'exp_start_date': start_time,
                'subject': task_data["subject"],
                'custom_assigneedoer': user
            },
            fields=['name']
        )
        if existing_task:
            print(f"Task already exists for employee {user} with start_time {start_time} and end_time {end_time}. Skipping creation.")
            return

        # Create the task if it doesn't exist
        task = frappe.new_doc('Task')
        task.subject = task_data["subject"]
        task.project = frappe.db.get_value("Project", {"project_name": task_data["project_name"]}, "name", cache=True)
        task.type = frappe.db.get_value("Task Type", {"name": task_data["task_type"]}, "name", cache=True)
        task.status = "Open"
        task.custom_master_task = task_data["name"]
        task.exp_end_date = end_time
        task.exp_start_date = start_time
        task.custom_expected_start_time = start_time.time().replace(microsecond=0)
        task.custom_expected_end_time = end_time.time().replace(microsecond=0)
        task.custom_assigneedoer = user
        task.description = task_data["details"]
        task.department = frappe.db.get_value("Employee", emp, "department", cache=True)
        task.custom_assignee_full_name = frappe.db.get_value("User",user, "full_name")
        task.custom_task_assigned_by = task_data["task_assigner"]
        task.save()

        attachments = frappe.get_all("Master Task Attachments", filters={'parent': task_data["name"]}, fields=['*'])
        print("Task Attachments:", attachments)
        for attachment in attachments:
            print(f"Processing attachment: {attachment}")
            file_url = attachment.attachment  # assuming "file" is the Attach field

            if file_url:
                # Avoid duplicate File entries
                exists = frappe.get_all("File", filters={
                    "file_url": file_url,
                    "attached_to_doctype": "Task",
                    "attached_to_name": task.name
                })
                if not exists:
                    file_doc = frappe.new_doc("File")
                    file_doc.file_url = file_url
                    file_doc.attached_to_doctype = "Task"
                    file_doc.attached_to_name = task.name
                    file_doc.save(ignore_permissions=True)

        frappe.db.commit()

        master_task_doc = frappe.get_doc("Master Tasks", task_data["name"])
        for watcher in master_task_doc.watchers:
            frappe.share.add(
                doctype=task.doctype,
                name=task.name,
                user=watcher.user,
                read=1,
            )
            watcher.shared = 1

        print(f"Task created for employee {employee} with start_time {start_time} and end_time {end_time}.")
    except Exception as e:
        print(f"Error creating task for employee {employee}: {str(e)}")
        frappe.log_error(f"Error creating task for employee {employee}: {str(e)}")

def send_recurring_watcher_email(task_data, watchers):
    if not watchers:
        return
    email_template_name = frappe.get_value("Email Template", "Recurring task watcher email", "name")
    if not email_template_name:
        frappe.log_error("Recurring task watcher email template not found")
        return
    email_template = frappe.get_doc("Email Template", email_template_name)
    email_subject = email_template.subject or "Recurring Task Notification"
    message = frappe.render_template(
        email_template.response_html or "{{ task_data }}",
        context={"task_data": task_data}
    )
    frappe.sendmail(
        recipients=watchers,
        subject=email_subject,
        message=message,
    )

def send_one_time_task_mail(task_data, watchers):
    if not watchers:
        return
    email_template_name = frappe.get_value("Email Template", "One time task watcher email", "name")
    if not email_template_name:
        frappe.log_error("One time task watcher email template not found")
        return
    email_template = frappe.get_doc("Email Template", email_template_name)
    email_subject = email_template.subject or "One Time Task Notification"
    message = frappe.render_template(
        email_template.response_html or "{{ task_data }}",
        context={"task_data":task_data}
    )
    frappe.sendmail(
        recipients=watchers,
        subject=email_subject,
        message=message,
    )

def string_to_time(value):
    """Normalize value into datetime.time"""
    if isinstance(value, str):
        # Normalize strings like '8:30:00' -> '08:30:00'
        return datetime.strptime(value.zfill(8), "%H:%M:%S").time()
    elif isinstance(value, time):
        return value
    elif value is None:
        return None
    else:
        raise TypeError(f"Invalid type for shift time: {type(value)}")