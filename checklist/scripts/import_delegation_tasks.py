import frappe
import pandas as pd
from datetime import datetime
from checklist.tasks import schedule_tasks
import logging

logging.basicConfig(
    filename=frappe.get_site_path("private", "logs", "task_import_errors.log"),
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

file_path = frappe.get_site_path(
    "private", "files", "Main_Delegation_Sheet_Manoj_Ornaments.xlsx"
)


def import_tasks_from_xlsx():
    count = 0
    task_count = 0
    sheet_task_count = 0

    email_mapping = {
        "SARIKA JAIN": "sarikajain.mopl@gmail.com",
        "SANDIP JAIN": "sandeepjain.mopl@gmail.com",
        "MUKESH PANDEY": "mukesh.mopl2017@gmail.com",
        "VISHWA SHAH": "vishwashah.mopl@gmail.com",
        "Aadit Neema": "aaditneema.mopl@gmail.com",
        "Viraj": "virajvirwadia.mopl@gmail.com",
        "Diya Shah": "diyashah.mopl@gmail.com",
        "AMOL KALMBATE": "amolkalambate.mopl@gmail.com",
        "SARIKA JAIN": "sarikajain.mopl@gmail.com",
        "DAYARAM VISHVAKARMA": "dayaram.mopl@gmail.com",
        "Nakul Parmar": "nakulparmar.mopl@gmail.com",
        "PRAMOD CHOUHAN": "gm@manojornaments.com",
        "GANESH CHORAGE": "ganeshchorage.mopl@gmail.com",
        "Chirag Chouhan": "manojcreationandinnovation@gmail.com",
        "Vinod Kumar": "qatarmanojornaments@gmail.com",
        "NIKITA SINGH": "nikitasingh.mopl@gmail.com",
        "Gaurav Jain": "gouravjain.mopl@gmail.com",
        "Gourav Jain": "gouravjain.mopl@gmail.com",
        "Nandini Shetty": "nandinishetty.mopl@gmail.com",
        "Nandani Mam": "nandinishetty.mopl@gmail.com",
        "Manali Kanade": "manalikanade.mopl@gmail.com",
        "DHRUMIT PARMAR": "dhrumitparmar.mopl@gmail.com",
        "KRISHNATH SUBHASH DUDHADE": "krishnatdudadhe.mopl@gmail.com",
        "DILIP GURJAR": "dilipgurjar.mopl@gmail.com",
        "Pruthika Padte": "pruthikapadte.mopl@gmail.com",
        "ANKUR B SOLANKI": "ankursolanki.mopl@gmail.com",
        "Pradnya Madam": "pradnyakargutkar.mopl@gmail.com",
        "Vanshi Jain": "vanshi.mopl@gmail.com",
        "SAURAV DAS": "mis@manojornaments.com",
        "Shreya Sanghvi": "shreyasanghvi.mopl@gmail.com",
        "PRAVIN JAGTAP": "pravinjagtap.mopl@gmail.com",
        "SANJAY SIR": "sanjay.mopl@gmail.com",
        "Sanjay sir": "sanjay.mopl@gmail.com",
        "sanjay sir": "sanjay.mopl@gmail.com",
        "Sanjay Sir": "sanjay.mopl@gmail.com",
        "Sanjay Sir": "sanjay.mopl@gmail.com",
        "Sanjay Sir": "sanjay.mopl@gmail.com",
        "Sanjay Sir,": "sanjay.mopl@gmail.com",
        "Sanjay Sir,": "sanjay.mopl@gmail.com",
        "Bhoomi Maam": "bhoomi.mopl@gmail.com",
        "Chetna Maam": "chetna.mopl@gmail.com",
        "Himanshu Shah": "himanshu.mopl@gmail.com",
        "Hitesh Vaishnav": "hiteshvishnav.mopl@gmail.com",
        "Yakuta Merchant": "trainermopl@gmail.com",
    }

    df_index = pd.read_excel(file_path, sheet_name="Index")
    for _, row in df_index.iterrows():
        sr_no = row.get("Header A")
        task_assign_date = row.get("Header B")
        assign_by = row.get("Header C")
        assign_to = row.get("Header D")
        description = row.get("Header E")
        first_date = row.get("Header G")
        revision_date_1 = row.get("Header H")
        revision_date_2 = row.get("Header I")
        revision_date_3 = row.get("Header J")
        revision_date_4 = row.get("Header K")
        final_date = row.get("Header L")
        status = row.get("Header N")
        completion_date = row.get("Header O")
        priority = row.get("Header T")
        task_status = row.get("Header U")

        dt1 = first_date if isinstance(first_date, datetime) else None
        dt2 = revision_date_1 if isinstance(revision_date_1, datetime) else None
        dt3 = revision_date_2 if isinstance(revision_date_2, datetime) else None
        dt4 = revision_date_3 if isinstance(revision_date_3, datetime) else None
        dt5 = revision_date_4 if isinstance(revision_date_4, datetime) else None
        dt6 = final_date if isinstance(final_date, datetime) else None
        datetimes = [dt1, dt2, dt3, dt4, dt5, dt6]
        valid_datetimes = [dt for dt in datetimes if dt is not None]
        if (
            valid_datetimes
            and not completion_date
            and max(valid_datetimes) > datetime(2025, 8, 23)
        ) or (status == "Pending" and max(valid_datetimes) > datetime(2025, 8, 1)):
            sheet_task_count+=1
            print("------> ", sheet_task_count, ": Conditions met for the following master task in the sheet. Following are the details: ")
            print(task_assign_date, " ", assign_by, " ", assign_to, " ",first_date, " ", revision_date_1, " ", revision_date_2, " ", revision_date_3, " ", revision_date_4, " ", final_date, " ", status, " ", priority, " ", task_status, " ")
            
            if assign_to not in email_mapping:
                print("Skipping assign to: ", assign_to)
                continue
            if assign_by not in email_mapping:
                print("Skipping assign by: ", assign_by)
                continue
            try:
                doc = frappe.new_doc("Master Tasks")
                doc.task_type = "One-Time"
                doc.subject = "Delegation Task"
                doc.active = 1
                doc.start_date = dt1.date()
                doc.end_date = dt1.date()
                doc.details = description
                doc.task_assigner = email_mapping[assign_by]
                child_row = doc.append("assignee_doers", {})
                child_row.employee = email_mapping[assign_to]
                doc.save()
                frappe.db.commit()
                schedule_tasks()
                count += 1
                print("created new master doc: ", count)

                related_sub_task = frappe.get_all(
                    "Task", filters={"custom_master_task": doc.name}, limit=1
                )
                if related_sub_task:
                    sub_task_doc_name = related_sub_task[0]["name"]
                    related_sub_task_doc = frappe.get_doc("Task", sub_task_doc_name)
                    task_count+=1
                    print("New task created: ", task_count)
                    related_sub_task_doc.priority = priority
                    datetimes.pop(0)
                    datetimes.pop()
                    current_date = dt1
                    for dt in datetimes:
                        if dt:
                            related_sub_task_doc.append(
                                "custom_reschedule_history",
                                {
                                    "rescheduled_on": current_date.date(),
                                    "from_date": current_date.date(),
                                    "to_date": dt.date(),
                                },
                            )
                            current_date = dt
                            related_sub_task_doc.exp_start_date = dt.date()
                            related_sub_task_doc.exp_end_date = dt.date()
                            related_sub_task_doc.save()
                            frappe.db.commit()
                        else:
                            break
            except Exception as e:
                print("error processing task with sr_no:", sr_no, "| Error:", str(e))
                logging.error("Error processing task with sr_no: %s | Error: %s", sr_no, str(e))
    print("total rows which met satisfy given conditions: ", sheet_task_count)
    print("total master task creted: ", count)
    print("total child task created: ", task_count)