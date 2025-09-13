# import frappe
# import re

# @frappe.whitelist()
# def add_dynamic_field(doctype, fieldname, fieldtype="Data", label=None):
#     """
#     Add a custom field dynamically to a Doctype after sanitizing the fieldname.
#     """
#     # Convert to lowercase, replace spaces with underscores, and remove special characters
#     sanitized_fieldname = re.sub(r'\W+', '_', fieldname.strip().lower())

#     # Default label (user-friendly name)
#     if not label:
#         label = fieldname.title()


    

#     # Prevent duplicate fields
#     if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": sanitized_fieldname}):
#         custom_field = frappe.get_doc({
#             "doctype": "Custom Field",
#             "dt": doctype,
#             "fieldname": sanitized_fieldname,
#             "label": label,
#             "fieldtype": fieldtype,
#             "insert_after": "description"  # Adjust position as needed
#         })
#         custom_field.insert(ignore_permissions=True)
#         frappe.db.commit()

#         return f"Field '{label}' ({sanitized_fieldname}) added successfully!"
    
#     return f"Field '{label}' already exists!"


import frappe
import re

@frappe.whitelist()
def add_dynamic_field(fieldname, fieldtype="Data", label=None):
    """
    Add a field directly to the ToDo Tasks Doctype.
    """
    # Convert to lowercase, replace spaces with underscores, and remove special characters
    sanitized_fieldname = re.sub(r'\W+', '_', fieldname.strip().lower())

    # Default label (user-friendly name)
    if not label:
        label = fieldname.title()

    # Check if the field already exists in the Doctype
    todo_meta = frappe.get_meta("ToDo Tasks")
    if any(field.fieldname == sanitized_fieldname for field in todo_meta.fields):
        return f"Field '{label}' already exists in ToDo Tasks!"

    # Add the field to the Doctype
    todo_meta.append("fields", {
        "fieldname": sanitized_fieldname,
        "label": label,
        "fieldtype": fieldtype
    })
    add_subject_field_to_custom_task()
    # Save the changes to the Doctype
    # frappe.db.commit()
    return f"Field '{label}' ({sanitized_fieldname}) added successfully to ToDo Tasks!"


# import frappe
# import re

# @frappe.whitelist()
# def add_dynamic_field_to_todo(fieldname, fieldtype="Data", label=None):
#     """
#     Add a custom field dynamically to the ToDo Tasks Doctype and persist it in the database.
#     """
#     # Convert to lowercase, replace spaces with underscores, and remove special characters
#     sanitized_fieldname = re.sub(r'\W+', '_', fieldname.strip().lower())

#     # Default label (user-friendly name)
#     if not label:
#         label = fieldname.title()

#     # Check if the field already exists in the Custom Field table
#     if frappe.db.exists("Custom Field", {"dt": "ToDo Tasks", "fieldname": sanitized_fieldname}):
#         return f"Field '{label}' already exists in ToDo Tasks!"

#     # Create the custom field
#     custom_field = frappe.get_doc({
#         "doctype": "Custom Field",
#         "dt": "ToDo Tasks",
#         "fieldname": sanitized_fieldname,
#         "label": label,
#         "fieldtype": fieldtype,
#         "insert_after": "description"  # Adjust position as needed
#     })
#     custom_field.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return f"Field '{label}' ({sanitized_fieldname}) added successfully to ToDo Tasks!"


# import frappe

def create_dynamic_field_child_table():
    if not frappe.db.exists("DocType", "Dynamic Field"):
        child_doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Dynamic Field",
            "module": "YourApp",
            "custom": 0,
            "istable": 1,
            "fields": [
                {
                    "fieldname": "field_label",
                    "label": "Field Label",
                    "fieldtype": "Data",
                    "reqd": 1
                },
                {
                    "fieldname": "fieldtype",
                    "label": "Field Type",
                    "fieldtype": "Select",
                    "options": "Data\nText\nInt\nDate\nAttach\nCheck",
                    "reqd": 1
                },
                {
                    "fieldname": "default_value",
                    "label": "Default Value",
                    "fieldtype": "Data"
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "permlevel": 0,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                }
            ]
        })
        child_doc.insert()
        frappe.db.commit()


def create_new_doctype():
    doctype = "Custom Task"
    doc = frappe.get_doc("DocType", doctype)
    existing_fieldnames = [df.fieldname for df in doc.fields]

    if "subject1" not in existing_fieldnames:
        new_field = {
            "fieldname": "subject1",
            "label": "Subject One",
            "fieldtype": "Data",
            "insert_after": "status",
            "doctype": "DocField",
            "parent": doctype,
            "parentfield": "fields",
            "parenttype": "DocType",
            "idx": len(doc.fields) + 1
        }

        doc.append("fields", new_field)
        doc.save()
        frappe.db.commit()
        frappe.msgprint("Field 'Subject' added to Custom Task")
    else:
        frappe.msgprint("Field already exists.")



@frappe.whitelist()
def user_with_employee_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT u.name, u.full_name
        FROM `tabUser` u
        WHERE EXISTS (
            SELECT 1 FROM `tabEmployee` e WHERE e.user_id = u.name and e.status = 'Active'
        )
        AND u.name LIKE %(txt)s
        ORDER BY u.name
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })