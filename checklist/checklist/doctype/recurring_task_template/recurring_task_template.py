# Copyright (c) 2025, Avi Root Info Solutions and contributors
# For license information, please see license.txt

import frappe
import re
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.query_builder import DocType, functions as fn
import json
from datetime import date
class RecurringTaskTemplate(Document):

    def validate(self):

        if not self.end_date:
            try:
                settings_doc = frappe.get_doc("Checklist Settings")
                maximum_task_limit = settings_doc.maximum_task_limit
            except Exception as e:
                print("Exception: ", str(e))

            if not maximum_task_limit:
                frappe.throw("Either specify the end date or define the maximum task limit in Checklist Settings.")

@frappe.whitelist()
def save_recurring_settings(docname, data):
        data = json.loads(data)
        doc = frappe.get_doc('Recurring Task Template', docname)

        doc.start_date = data.get('start_date')
        doc.end_date = data.get('end_date')
        doc.repeat_interval = data.get('repeat_interval')
        doc.interval_unit = data.get('interval_unit')
        doc.repeat_days = json.dumps(data.get('repeat_days'))
        doc.month_repeat_type = data.get('monthly_repeat_type')
        doc.year_repeat_type = data.get('yearly_repeat_type')

        doc.save()
        return "Success"

@frappe.whitelist()
def create_master_task(doc):

    if not frappe.db.exists("Employee", {"user_id": "Administrator"}):
        admin_employee = frappe.new_doc("Employee")
        admin_employee.first_name = "Administrator"
        admin_employee.gender = "Male"
        admin_employee.date_of_birth = date(2000, 1, 1)
        admin_employee.date_of_joining = date.today()
        admin_employee.status = "Active"
        admin_employee.user_id = "Administrator"
        admin_employee.company = frappe.get_all("Company", pluck="name", order_by="creation asc", limit=1)[0]
        admin_employee.create_user_permission = 0
        admin_employee.insert()


    data = json.loads(doc) if isinstance(doc, str) else doc

    new_doc = frappe.new_doc("Master Tasks")
    new_doc.task_type = data.get("task_type")
    new_doc.subject = data.get("subject")
    new_doc.interval_unit = data.get("interval_unit")
    new_doc.repeat_interval = data.get("repeat_interval")
    new_doc.repeat_days = data.get("repeat_days")
    new_doc.year_repeat_type = data.get("year_repeat_type")
    new_doc.month_repeat_type = data.get("month_repeat_type")
    new_doc.start_date = data.get("start_date")
    new_doc.end_date = data.get("end_date")
    new_doc.details = data.get("details")

    # get oldest user
    user = frappe.get_all("User", pluck="name", order_by="creation asc", limit=1)
    if user:
        row = new_doc.append("assignee_doers", {})
        row.employee = user[0]

    try:
        new_doc.save(ignore_permissions=True)
        return {"status": "success", "name": new_doc.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Master Task Error")
        return {"status": "failed", "error": str(e)}
