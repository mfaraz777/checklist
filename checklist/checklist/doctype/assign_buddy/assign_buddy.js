// Copyright (c) 2025, Avi Root Info Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Assign Buddy", {
	onload: function (frm) {
		frm.set_query("assigner_username", function () {
			return {
				filters: {
					email: frappe.session.user,
				},
			};
		});

		if (!frm.doc.assigner_username) {
			frm.set_value("assigner_username", frappe.session.user);
		}

		frappe.call({
			method: "checklist.checklist.doctype.assign_buddy.assign_buddy.get_approver",
			args: {
				user: frappe.session.user,
			},
			callback: function (r) {
				if (r.message && !frm.doc.approver) {
					frm.set_value("approver", r.message.full_name);
				}
			},
		});
	},
    start_date: function (frm) {
        populate_task(frm);
    },
    end_date: function (frm) {
        populate_task(frm);
    },
    assigner_username: function (frm) {
        populate_task(frm);
    }
});

function populate_task(frm) {
    if (!frm.doc.assigner_username || !frm.doc.start_date || !frm.doc.end_date) {
        return;
    }

    let end_datetime = frm.doc.end_date;
    if (end_datetime && end_datetime.length === 10) {
        end_datetime += ' 23:59:59';
    }

    frappe.call({
        method: 'checklist.checklist.doctype.assign_buddy.assign_buddy.get_task_data',
        args: {
            start_date: frm.doc.start_date,
            end_datetime: frm.doc.end_date,
            task_assignee: frm.doc.assigner_username
        },
        callback: function(r) {
            if (r.message) {
                frm.clear_table('tasks');
                r.message.forEach(task => {
                    let row = frm.add_child('tasks');
                    row.task = task.name;
                    row.start_date = task.exp_start_date;
                    row.end_date = task.exp_end_date;
                    row.status = task.status;
                    row.subject = task.subject;
                });
                frm.refresh_field('tasks');
            }
        }
    });
}
