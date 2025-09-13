
import frappe
import datetime

@frappe.whitelist()
def get_completed_task_ontime():
    """
    Check if a task was completed on time.
    """
    roles = frappe.get_roles(frappe.session.user)
    if "Checklist Admin" in roles:
        tasks = frappe.get_all(
            "Task",
            filters={"status": "Completed"},
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )
    else:
        tasks = frappe.get_all(
            "Task",
            filters={"status": "Completed", "custom_assigneedoer": frappe.session.user},
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )

    completed_tasks = 0
    for task in tasks:
        if not task.completed_on or not task.exp_end_date:
            continue
        if isinstance(task.exp_end_date, datetime.datetime):
        # Ensure both dates are datetime objects before comparison
            if task.completed_on <= task.exp_end_date.date():
                completed_tasks += 1
        elif isinstance(task.exp_end_date, datetime.date):
            if task.completed_on <= task.exp_end_date:
                completed_tasks += 1

    return completed_tasks

@frappe.whitelist()
def get_completed_tasks():
    """
    Get the total number of completed tasks for the user.
    """
    roles = frappe.get_roles(frappe.session.user)
    if "Checklist Admin" in roles:
        tasks = frappe.get_all(
            "Task",
            filters={"status": "Completed"},
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )
    else:
        tasks = frappe.get_all(
            "Task",
            filters={"status": "Completed", "custom_assigneedoer": frappe.session.user},
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )

    return len(tasks)

@frappe.whitelist()
def get_open_tasks():
    """
    Get the total number of open tasks for the user.
    """
    roles = frappe.get_roles(frappe.session.user)
    if "Checklist Admin" in roles:
        tasks = frappe.get_all(
            "Task",
            filters={"status": "Open"},
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )
    else:
        tasks = frappe.get_all(
            "Task",
            filters={"status": "Open", "custom_assigneedoer": frappe.session.user},
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )

    return len(tasks)

@frappe.whitelist()
def get_overdue_tasks():
    """
    Get the number of overdue tasks for the user.
    """
    roles = frappe.get_roles(frappe.session.user)
    if "Checklist Admin" in roles:
        tasks = frappe.get_all(
            "Task",
            filters={
                "status": "Overdue",
            },
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )
    
    else:
        tasks = frappe.get_all(
            "Task",
            filters={
                "status": "Overdue",
                "custom_assigneedoer": frappe.session.user
            },
            fields=["name", "subject", "completed_on", "exp_end_date"]
        )

    return len(tasks)

@frappe.whitelist()
def task_completed_late():
    """
    Check if a task was completed late.
    """
    tasks = frappe.get_all(
        "Task",
        filters={"status": "Completed","custom_assigneedoer": frappe.session.user},
        fields=["name", "subject", "completed_on", "exp_end_date"]
    )
    
    late_tasks = 0
    for task in tasks:
        if not task.completed_on or not task.exp_end_date:
            continue
        if task.completed_on > task.exp_end_date:
            late_tasks += 1

    return late_tasks