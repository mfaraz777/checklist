import frappe

def create_default_projects():
    default_projects = ["Checklist OneTime", "Checklist Recurring"]

    for project_name in default_projects:
        if not frappe.db.exists("Project", {"project_name": project_name}):
            frappe.get_doc({
                "doctype": "Project",
                "project_name": project_name,
                "status": "Open"
            }).insert(ignore_permissions=True)
    create_default_task_types()

def create_default_task_types():
    task_types = [
        {"task_type": "One-Time", "description": "One-time checklist tasks"},
        {"task_type": "Recurring", "description": "Recurring checklist tasks"}
    ]

    for task_type in task_types:
        if not frappe.db.exists("Task Type", {"name": task_type["task_type"]}):
            frappe.get_doc({
                "doctype": "Task Type",
                "name": task_type["task_type"],
                "description": task_type["description"]
            }).insert(ignore_permissions=True)
