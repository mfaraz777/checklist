# Copyright (c) 2025, Avi Root Info Solutions and contributors
# For license information, please see license.txt

import frappe
import re
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.query_builder import DocType, functions as fn


class MasterTasks(Document):

    original_assignee_list = None

    def validate(self):

        if self.task_type == "Recurring" and not self.end_date:
            try:
                settings_doc = frappe.get_doc("Checklist Settings")
                maximum_task_limit = settings_doc.maximum_task_limit
            except Exception as e:
                print("Exception: ", str(e))

            if not maximum_task_limit:
                frappe.throw("For Recurring tasks, either specify the end date or define the maximum task limit in Checklist ettings.")

        if not self.get("__islocal"):
            original_doc = frappe.get_doc(self.doctype, self.name)
            original_assignee_list = [
                assignee.employee for assignee in original_doc.assignee_doers
            ]
            setattr(self, "original_assignee_list", original_assignee_list)
            #delete tasks if check is removed.
            if not self.active:
                Task = DocType("Task")
                query = (
                        frappe.qb.from_(Task)
                        .select(Task.name)
                        .where(
                            (Task.custom_master_task == self.name)
                            & (Task.status == "Open")
                            & (
                                fn.Timestamp(Task.exp_end_date, Task.custom_expected_end_time) >= now_datetime()
                            )
                        )
                    )

                tasks = query.run(as_dict=True)
                #tasks = frappe.get_all("Task", filters = {"custom_master_task": self.name, "status": "Open", "exp_end_date": (">=", nowdate())})
                for task in tasks:
                    task_doc = frappe.get_doc("Task", task.name)
                    related_assign_buddy_list = frappe.get_all("Assign Buddy Task", filters = {"task" : task.name})
                    if related_assign_buddy_list:
                        for related_assign_buddy_doc_name in related_assign_buddy_list:
                            related_assign_buddy_doc = frappe.get_doc("Assign Buddy Task", related_assign_buddy_doc_name)
                            related_assign_buddy_doc.delete()
                    task_doc.delete()

        for watcher in self.watchers:
            if not watcher.shared:
                tasks = frappe.get_all("Task", filters = {"custom_master_task": self.name})
                for task in tasks:
                    frappe.share.add(
                        doctype=task.doctype,
                        name=task.name,
                        user=watcher.user,
                        read=1,
                    )
                watcher.shared = 1

    def before_save(self):
        if not self.time_sensitive:
            if self.from_time and self.to_time:
                self.from_time = None
                self.to_time = None
        fields_data = self.dynamic_fields
        self.create_dynamic_field_table(fields_data)

        email_list = None
        original_assignee_list = getattr(self, "original_assignee_list", None)
        new_assignee_list = [assignee.employee for assignee in self.assignee_doers]
        if original_assignee_list:
            # Editing existing doc => Email only newly added employees
            email_list = list(set(new_assignee_list) - set(original_assignee_list))
        else:
            # Is a new doc => Email all
            email_list = new_assignee_list
        if email_list:
            for assignee in email_list:
                employee_name = frappe.get_value(
                    "Employee",
                    {"company_email": assignee},
                    "name",
                )
                if employee_name:
                    employee_doc = frappe.get_doc("Employee", employee_name)
                    try:
                        frappe.sendmail(
                            recipients=[employee_doc.company_email],
                            subject=f"Hi, {employee_doc.employee_name}",
                            message=f"You have been assigned task {self.subject}",
                            delayed=False,
                        )
                    except Exception as e:
                        frappe.msgprint(f"Email failed: {str(e)}")

    def create_dynamic_field_table(self, fields_data, label=None):
        """Create or update a child table for dynamic fields."""
        if not fields_data:
            return
        try:
            doctype_name = f"Dynamic Form {self.name}"
            if not frappe.db.exists("DocType", doctype_name):
                # Create the Doctype if it does not exist
                child_doc = frappe.get_doc(
                    {
                        "doctype": "DocType",
                        "name": doctype_name,
                        "module": "Checklist",
                        "custom": 1,
                        "issingle": 0, 
                        "istable": 0,
                        "fields": [
                            {
                                "fieldname": "master_task",
                                "label": "Parent",
                                "fieldtype": "Link",
                                "options": "Master Tasks",
                                "default": self.name,
                                "hidden": 1,
                            },
                            {
                                "fieldname": "child_task",
                                "label": "Child",
                                "fieldtype": "Link",
                                "options": "Task",
                                "hidden": 1,
                            },
                            {
                                "fieldname": "due_date",
                                "label": "Due Date",
                                "fieldtype": "Datetime",
                                "hidden": 1,
                            },
                        ],
                        "permissions": [
                            {
                                "role": "System Manager",
                                "permlevel": 0,
                                "read": 1,
                                "write": 1,
                                "create": 1,
                                "delete": 1,
                            },
                            {
                                "role": "Checklist Admin",
                                "permlevel": 0,
                                "read": 1,
                                "write": 1,
                                "create": 1,
                                "delete": 1,
                            },
                            {
                                "role": "Checklist User",
                                "permlevel": 0,
                                "read": 1,
                                "write": 1,
                                "create": 1,
                                "delete": 0,
                            }
                        ],
                    }
                )
                child_doc.insert(ignore_permissions=True)
            else:
                # Fetch the existing Doctype
                child_doc = frappe.get_doc("DocType", doctype_name)

            # Maintain a set of existing fieldnames for comparison
            existing_fieldnames = {field.fieldname for field in child_doc.fields}

            # Add or update fields
            for field in fields_data:
                if not field.fieldname or not field.field_type:
                    continue
                field_name = field.fieldname
                field_type = field.field_type
                mandatory = field.mandatory

                # Convert to lowercase, replace spaces with underscores, and remove special characters
                sanitized_fieldname = re.sub(r"\W+", "_", field_name.strip().lower())
                # Set the label dynamically for each field
                field_label = label if label else field_name.title()
                if sanitized_fieldname in existing_fieldnames:
                    # Update existing field
                    for existing_field in child_doc.fields:
                        if existing_field.fieldname == sanitized_fieldname:
                            existing_field.label = field_label
                            existing_field.fieldtype = field_type
                            break
                else:
                    # Add new field
                    child_doc.append(
                        "fields",
                        {
                            "fieldname": sanitized_fieldname,
                            "label": field_label,
                            "fieldtype": field_type,
                            "doctype": "DocField",
                            "parent": doctype_name,
                            "parentfield": "fields",
                            "parenttype": "DocType",
                            "idx": len(child_doc.fields) + 1,
                            "reqd": mandatory,
                        },
                    )

            # Remove fields that are not in the new fields_data
            new_fieldnames = {
                re.sub(r"\W+", "_", field.fieldname.strip().lower())
                for field in fields_data
                if field.fieldname
            }
            fields_to_remove = [
                field
                for field in child_doc.fields
                if field.fieldname not in new_fieldnames
                and field.fieldname not in ["master_task", "child_task"]
            ]
            for field in fields_to_remove:
                child_doc.remove(field)

            # Save the changes
            child_doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(
                f"Error creating or updating child table: {str(e)}",
                "Dynamic Field Creation Error",
            )
            raise ValueError("Failed to create or update dynamic field child table.")


@frappe.whitelist()
def save_recurring_settings(docname, data):
        print("Data received in save_recurring_settings:", data)
        import json
        data = json.loads(data)

        print("Parsed data:", data)
        print("Docname:", docname)

        doc = frappe.get_doc('Master Tasks', docname)

        doc.start_date = data.get('start_date')
        doc.end_date = data.get('end_date')
        doc.repeat_interval = data.get('repeat_interval')
        doc.interval_unit = data.get('interval_unit')
        doc.repeat_days = json.dumps(data.get('repeat_days'))
        doc.month_repeat_type = data.get('monthly_repeat_type')
        doc.year_repeat_type = data.get('yearly_repeat_type')

        doc.save()
        return "Success"