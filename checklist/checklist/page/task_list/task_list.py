import json
import frappe
from frappe.utils import now
from datetime import date

STANDARD_FIELDS = ["due_date"]


@frappe.whitelist()
def get_tasks(start_date, end_date, status, user, page=1, page_size=10):
    try:
        # Check if the user has permission to view tasks
        if not frappe.has_permission("Task", "read"):
            frappe.throw("You do not have permission to view tasks.")

        # Convert page and page_size to integers
        page = int(page)
        page_size = int(page_size)

        # Calculate start index for pagination
        start_idx = (page - 1) * page_size

        print("Fetching tasks for user:", frappe.session.user)
        roles = frappe.get_roles(frappe.session.user)

        # Build the base query
        if "Checklist Admin" in roles:
            # Show all tasks
            conditions = []
            params = []

            if start_date and end_date:
                conditions.append("(t.exp_start_date <= %s AND t.exp_end_date >= %s)")
                params.extend([end_date, start_date])
            if status and status != "All":
                conditions.append("t.status = %s")
                params.append(status)
            if user and user != "All":
                conditions.append("t.custom_assigneedoer = %s")
                params.append(user)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            # Get total count
            count_query = f"""
                SELECT COUNT(*) 
                FROM `tabTask` t
                {where_clause}
            """
            total_count = frappe.db.sql(count_query, params, as_dict=False)[0][0]

            # Get paginated tasks with stable ordering
            query = f"""
                SELECT t.subject, t.name, t.status, t.exp_end_date, t.custom_master_task, 
                       t.description, t.exp_start_date, t.custom_assignee_full_name
                FROM `tabTask` t
                {where_clause}
                ORDER BY t.creation DESC, t.name ASC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, start_idx])
            tasks = frappe.db.sql(query, params, as_dict=True)

        elif "Checklist User" in roles:
            # Show only current user's tasks
            conditions = ["t.custom_assigneedoer = %s"]
            params = [frappe.session.user]

            if start_date and end_date:
                conditions.append("(t.exp_start_date <= %s AND t.exp_end_date >= %s)")
                params.extend([end_date, start_date])
            if status and status != "All":
                conditions.append("t.status = %s")
                params.append(status)

            where_clause = "WHERE " + " AND ".join(conditions)

            # Get total count
            count_query = f"""
                SELECT COUNT(*) 
                FROM `tabTask` t
                {where_clause}
            """
            total_count = frappe.db.sql(count_query, params, as_dict=False)[0][0]

            # Get paginated tasks with stable ordering
            query = f"""
                SELECT t.subject, t.name, t.status, t.exp_end_date, t.custom_master_task, 
                       t.description, t.exp_start_date
                FROM `tabTask` t
                {where_clause}
                ORDER BY t.creation DESC, t.name ASC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, start_idx])
            tasks = frappe.db.sql(query, params, as_dict=True)

        print(
            f"Found {len(tasks)} tasks on page {page} out of {total_count} total tasks"
        )

    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        return {"tasks": [], "total_count": 0, "has_more": False}

    custom_fields = []
    data = []
    for task in tasks:
        if not task.get("custom_master_task"):
            continue

        docname = f"Dynamic Form {task.custom_master_task}"
        try:
            master_task = frappe.get_doc("Master Tasks", task.custom_master_task)

            if master_task.dynamic_fields:
                try:
                    metadata = frappe.get_meta(docname)
                    custom_fields = metadata.fields
                except:
                    custom_fields = []
        except:
            custom_fields = []

        all_fields = list(custom_fields) + [
            {
                "fieldname": f,
                "label": f.replace("_", " ").title(),
                "fieldtype": "Datetime",
                "hidden": 1,
            }
            for f in STANDARD_FIELDS
        ]
        all_fields += [
            {
                "fieldname": "reschedule_remarks",
                "label": "Reschedule Remarks",
                "fieldtype": "Small Text",
                "hidden": 1,
            }
        ]

        task_data = {
            "subject": task.subject,
            "description": task.description or "",
            "status": task.status,
            "due_date": task.exp_end_date,
            "name": task.name,
            "fields_to_display": all_fields,
            "exp_start_date": task.exp_start_date,
            "custom_assignee_full_name": task.get("custom_assignee_full_name", "")
            or "",
        }
        data.append(task_data)
        # Return tasks with pagination info
    has_more = (start_idx + len(tasks)) < total_count
    return {"tasks": data, "total_count": total_count, "has_more": has_more}


@frappe.whitelist()
def update_task(name, updates):
    """
    Update the status of a task.
    """
    reschedule_frequency = frappe.get_value(
        "Checklist Settings", "Checklist Settings", "reschedule_count"
    )
    data = json.loads(updates)
    task = frappe.get_doc("Task", name)
    current_due_date = task.exp_end_date
    if data.get("status") == "Completed":
        task.status = data.get("status")
        task.completed_by = frappe.session.user
        task.completed_on = now()
    elif data.get("status") == "Reschedule":
        task.exp_end_date = data.get("due_date")
        task.custom_reschedule_count = (
            task.custom_reschedule_count + 1 if task.custom_reschedule_count else 1
        )
        if reschedule_frequency and task.custom_reschedule_count > int(
            reschedule_frequency
        ):
            frappe.throw(
                f"Task cannot be rescheduled more than {reschedule_frequency} times. Please complete the task or escalate it."
            )
        task.append(
            "custom_reschedule_history",
            {
                "rescheduled_on": date.today(),
                "from_date": current_due_date,
                "to_date": data.get("due_date"),
                "rescheduled_by": frappe.session.user,
                "reschedule_remarks": data.get("reschedule_remarks") or "",
            },
        )
        task.save()
        frappe.db.commit()
        return "success"

    # Update dynamic fields
    data.pop("status", None)
    data["child_task"] = task.name

    master_task = frappe.get_doc("Master Tasks", task.custom_master_task)
    if master_task.dynamic_fields:
        metadata_doc = f"Dynamic Form {task.custom_master_task}"
        metadata = frappe.new_doc(metadata_doc)
        for key, val in data.items():
            metadata.set(key, val)
        metadata.insert()
    task.save()
    frappe.db.commit()
    return "success"


@frappe.whitelist()
def get_all_users():
    roles = frappe.get_roles(frappe.session.user)
    if "Checklist Admin" in roles:
        users = frappe.get_all(
            "User",
            fields=["name", "full_name"],
            filters={"enabled": 1},
            order_by="full_name"
        )
        return users
    else:
        users = frappe.get_all(
            "User",
            fields=["name", "full_name"],
            filters={"name": frappe.session.user},
        )
        return users
