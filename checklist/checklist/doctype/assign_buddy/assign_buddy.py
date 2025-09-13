# Copyright (c) 2025, Avi Root Info Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import date, datetime, time
from frappe.utils import getdate
from frappe.utils import get_url

class AssignBuddy(Document):

    def validate(self):
        if self.buddy_username == self.assigner_username:
            frappe.throw("Cannot re-assign the task to self")
        if self.end_date < self.start_date:
            frappe.throw("End date cannot be before start date")

    def before_submit(self):

        user = frappe.session.user
        allowed = False

        if "Checklist Admin" in frappe.get_roles(user):
            allowed = True
        reports_to = get_approver(self.assigner_username)
        if reports_to:
            if frappe.session.user == reports_to["username"]:
                allowed = True
        if not allowed:
            frappe.throw("You are not authorized to approve this document.")

        if isinstance(self.end_date, date) and not isinstance(self.end_date, datetime):
            end_datetime = datetime.combine(self.end_date, time(23, 59, 59))
        else:
            end_datetime = self.end_date

        tasks = get_task_data(self.start_date, end_datetime, self.assigner_username)
        for task in tasks:
            task_doc = frappe.get_doc("Task", task["name"])
            task_doc.custom_assigneedoer = self.buddy_username
            task_doc.save()

        task_url_prefix = f"{get_url()}"

        try:
            email_template = frappe.get_doc("Email Template", "Task Buddy Assigner")
            subject = email_template.subject
            message_context = {"doc": self, "get_url": get_url}  # expose the function directly
            message = frappe.render_template(
                email_template.response_html, context=message_context
            )
            assigner_email = self.assigner_username
            frappe.sendmail(
                recipients=[assigner_email],
                subject=subject,
                message=message,
                reference_doctype="Assign Buddy",
                reference_name=self.name,
            )
        except Exception:
            frappe.msgprint(f"Sending email to assigner failed. An error occured.")

        try:
            email_template = frappe.get_doc("Email Template", "Task Buddy Assignee")
            subject = email_template.subject
            message_context = {"doc": self, "get_url": get_url}
            message = frappe.render_template(
                email_template.response_html, context=message_context
            )
            assignee_email = self.buddy_username
            frappe.sendmail(
                recipients=[assignee_email],
                subject=subject,
                message=message,
                reference_doctype="Assign Buddy",
                reference_name=self.name,
            )
        except Exception:
            frappe.msgprint(f"Sending email to assignee failed. An error occured.")


@frappe.whitelist()
def get_approver(user):
    employee_doc_name = frappe.get_value("Employee", {"user_id": user}, "name")
    if employee_doc_name:
        employee_doc = frappe.get_doc("Employee", employee_doc_name)
        reports_to = employee_doc.reports_to
        if reports_to:
            reports_to_employee_userid = frappe.get_value(
                "Employee", {"name": reports_to}, "user_id"
            )
            if reports_to_employee_userid:
                full_name = frappe.get_value(
                    "User", reports_to_employee_userid, "full_name"
                )
                return {"username": reports_to_employee_userid, "full_name": full_name}


@frappe.whitelist()
def get_task_data(start_date, end_datetime, task_assignee):

    if type(end_datetime) is str:
        end_datetime = getdate(end_datetime)

    tasks = frappe.db.get_list(
        "Task",
        filters={
            "status": ["not in", ["Completed", "Cancelled"]],
            "custom_assigneedoer": task_assignee,
            "exp_start_date": ["<=", end_datetime],
            "exp_end_date": [">=", start_date],
        },
        fields=["name", "exp_start_date", "exp_end_date", "status", "subject"],
    )
    return tasks
