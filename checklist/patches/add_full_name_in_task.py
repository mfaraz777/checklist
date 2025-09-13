import frappe


def execute():
    tasks = frappe.get_all(
        "Task", fields=["name", "custom_assignee_full_name", "custom_assigneedoer"]
    )

    for t in tasks:
        if not t.custom_assignee_full_name and t.custom_assigneedoer:
            full_name = frappe.db.get_value("User", t.custom_assigneedoer, "full_name")
            if full_name:
                frappe.db.set_value(
                    "Task",
                    t.name,
                    "custom_assignee_full_name",
                    full_name,
                    update_modified=False,
                )
