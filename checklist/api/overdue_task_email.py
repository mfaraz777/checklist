import frappe
from datetime import datetime, date, time
from frappe.utils import get_url
from datetime import datetime, date, time

def check_email_time_and_send_mail():
    settings = frappe.get_single("Checklist Settings")
    last_overdue_email_sent_date = None
    if settings.last_overdue_email_sent_date:
        last_overdue_email_sent_date = datetime.strptime(settings.last_overdue_email_sent_date, "%Y-%m-%d").date()

    if not settings.send_daily_summary:
        return
    if last_overdue_email_sent_date == date.today():
        return
    now = datetime.now()
    if settings.time:
        try:
            parsed_time = datetime.strptime(settings.time, "%H:%M:%S").time()
        except ValueError:
            parsed_time = datetime.strptime(settings.time, "%H:%M").time()
        send_time = datetime.combine(date.today(), parsed_time)
    else:
        send_time = datetime.combine(date.today(), time(9, 0))

    if now > send_time:
        send_overdue_email()
        settings.last_overdue_email_sent_date = date.today().isoformat()
        settings.save()
        frappe.db.commit()

def send_overdue_email():
    base_url = get_url()
    all_users = frappe.get_all("User", filters={"enabled": 1})
    email_template = frappe.get_doc("Email Template", "Task Overdue Email to Watcher")

    for user in all_users:
        user_doc = frappe.get_doc("User", user.name)

        docshare_list = frappe.get_all(
            "DocShare",
            fields=["share_name"],
            filters={"user": user_doc.name, "share_doctype": "Task"},
        )

        task_list = []
        for docshare in docshare_list:
            try:
                task_doc = frappe.get_doc("Task", docshare.share_name)
                if task_doc.status == "Overdue":
                    task_list.append(task_doc.name)
            except frappe.DoesNotExistError:
                continue  # Task might have been deleted

        if task_list:
            message_context = {
                "task": task_list,
                "base_url": base_url,
                "watcher_first_name": user_doc.first_name,
            }
            message = frappe.render_template(
                email_template.response_html, context=message_context
            )
            frappe.sendmail(
                recipients=[user_doc.email],
                subject=email_template.subject,
                message=message,
            )
            frappe.db.commit()
