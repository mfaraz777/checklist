frappe.pages["task-list"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Action Items",
		single_column: true,
	});

	page.add_inner_button("Assign Buddy", () => {
		frappe.new_doc("Assign Buddy");
	});

	// Style the custom button
	page.inner_toolbar.find('button:contains("Assign Buddy")').css({
		"background-color": "black",
		color: "white",
		border: "1px solid black",
	});

	// -------------------- Filters --------------------
	let $filters = $(`
    <div class="row mt-3 mb-2">
        <div class="col-sm-3">
            <label for="filter-start-date"><small class="text-muted">Start Date</small></label>
            <input type="date" id="filter-start-date" class="form-control">
        </div>
        <div class="col-sm-3">
            <label for="filter-end-date"><small class="text-muted">End Date</small></label>
            <input type="date" id="filter-end-date" class="form-control">
        </div>
        <div class="col-sm-3">
            <label for="filter-status"><small class="text-muted">Status</small></label>
            <select id="filter-status" class="form-control">
                <option value="">All</option>
                <option value="Open">Open</option>
                <option value="Completed">Completed</option>
                <option value="Overdue">Overdue</option>
            </select>
        </div>
        <div class="col-sm-3">
            <label for="filter-user"><small class="text-muted">Employee</small></label>
            <select id="filter-user" class="form-control">
                <option value="">All</option>
            </select>
        </div>
    </div>
    `).appendTo(page.body);
	let today = frappe.datetime.get_today();
	$filters.find("#filter-start-date").val(today);
	$filters.find("#filter-end-date").val(today);

	// Populate employee dropdown
	frappe.call({
		method: "checklist.checklist.page.task_list.task_list.get_all_users",
		callback: function (r) {
			if (r.message) {
				const employeeSelect = $filters.find("#filter-user");

				// Add options first
				r.message.forEach((employee) => {
					employeeSelect.append(
						`<option value="${employee.name}">${
							employee.full_name || employee.name
						}</option>`
					);
				});

				// Then apply select2
				employeeSelect.select2({
					placeholder: "Select Employee",
					allowClear: true,
					width: "100%",
				});

				// Change handler
				employeeSelect.on("change", function () {
					load_tasks(false);
				});
			}
		},
	});

	// -------------------- Table --------------------
	let $table = $('<table class="table table-bordered mt-3">').appendTo(page.body);
	let $thead;
	if (frappe.user.has_role("Checklist Admin")) {
		$thead = $(
			"<thead><tr><th>Tasks</th><th>Assignee</th><th>Status</th><th>Start Date</th><th>Due Datetime</th><th>Actions</th></tr></thead>"
		).appendTo($table);
	} else {
		$thead = $(
			"<thead><tr><th>Tasks</th><th>Status</th><th>Start Date</th><th>Due Datetime</th><th>Actions</th></tr></thead>"
		).appendTo($table);
	}
	let $tbody = $("<tbody>").appendTo($table);

	// -------------------- Show More + Spinner --------------------
	let $showMoreContainer = $(`
        <div class="text-center mt-3 d-flex justify-content-center align-items-center" id="show-more-container">
            <button class="btn btn-default btn-sm mr-2" id="show-more-btn">Show More</button>
            <div class="spinner-border text-primary spinner-sm ml-2" id="loading-spinner" role="status" style="display: none;">
                <span class="sr-only">Loading...</span>
            </div>
            <span id="task-counter" class="ml-3 text-muted"></span>
        </div>
    `).appendTo(page.body);

	// Pagination state
	let allTasks = [];
	let currentPage = 1;
	let isLoading = false;
	let hasMoreTasks = true;
	const pageSize = 10;

	// -------------------- Load Tasks --------------------
	function load_tasks(append = false) {
		if (isLoading) return;
		isLoading = true;

		if (append) {
			$("#loading-spinner").show();
			$("#show-more-btn").prop("disabled", true);
		} else {
			currentPage = 1; // reset when filters change or first load
		}

		let filters = {
			start_date: $("#filter-start-date").val(),
			end_date: $("#filter-end-date").val(),
			status: $("#filter-status").val(),
			user: $("#filter-user").val() || "",
			page: currentPage,
			page_size: pageSize,
		};

		frappe.call({
			method: "checklist.checklist.page.task_list.task_list.get_tasks",
			args: filters,
			callback: function (r) {
				isLoading = false;
				$("#loading-spinner").hide();
				$("#show-more-btn").prop("disabled", false);

				if (r.message) {
					const response = r.message;
					if (append) {
						allTasks = [...allTasks, ...response.tasks];
					} else {
						allTasks = response.tasks;
					}
					hasMoreTasks = response.has_more;
					renderTasks(append);
					let totalShown = allTasks.length;
					let totalAvailable = response.total_count || 0;
					$("#task-counter").text(`Tasks ${totalShown} of ${totalAvailable}`);

					if (hasMoreTasks && allTasks.length > 0) {
						$("#show-more-container").show();
					} else {
						$("#show-more-container").hide();
					}
				}
			},
		});
	}

	// -------------------- Render Tasks --------------------
	function renderTasks(append = false) {
		if (!append) {
			$tbody.empty();
		}

		if (allTasks.length > 0) {
			const startIndex = append ? (currentPage - 1) * pageSize : 0;
			const tasksToRender = allTasks.slice(startIndex);

			tasksToRender.forEach((task) => {
				if ($tbody.find(`tr[data-task-id="${task.name}"]`).length > 0) {
					return;
				}

				let $link = $(`<a href="#" class="task-link">${task.subject}</a>`);
				let $viewBtn = $(`<button class="btn btn-sm btn-primary">View</button>`);
				let extraColumn = "";

				if (frappe.user_roles.includes("Checklist Admin")) {
					extraColumn = `<td>${task.custom_assignee_full_name}</td>`;
				}

				let $row = $(`<tr data-task-id="${task.name}">
                    <td></td>
                    ${extraColumn}
                    <td>${task.status}</td>
                    <td>${task.exp_start_date}</td>
                    <td>${task.due_date}</td>
                    <td></td>
                </tr>`);

				$row.find("td:first").append($link);
				$row.find("td:last").append($viewBtn);

				// Task link click handler
				$link.on("click", function (e) {
					e.preventDefault();
					if (task.status === "Completed") {
						frappe.msgprint("Kudos ! Your Task is already Completed.");
					} else {
						let dialog_fields = task.fields_to_display.map((field) => ({
							label: field.label,
							fieldname: field.fieldname,
							fieldtype: field.fieldtype,
							default: field.default || "",
							hidden: field.hidden,
						}));

						let dialog = new frappe.ui.Dialog({
							title: "Update Task",
							fields: [
								{
									label: "Task Name",
									fieldname: "name",
									fieldtype: "Data",
									default: task.subject,
									read_only: 1,
								},
								{
									label: "Status",
									fieldname: "status",
									fieldtype: "Select",
									options: ["Reschedule", "Completed"],
									default: task.status,
									onchange: function () {
										let selected_status = dialog.get_value("status");
										if (selected_status === "Reschedule") {
											task.fields_to_display.forEach((field) => {
												if (
													["due_date", "exp_end_date"].includes(
														field.fieldname
													)
												) {
													dialog.set_df_property(
														field.fieldname,
														"hidden",
														0
													);
													dialog.set_df_property(
														field.fieldname,
														"reqd",
														field.fieldname === "due_date"
													);
												} else if (
													field.fieldname === "reschedule_remarks"
												) {
													dialog.set_df_property(
														field.fieldname,
														"hidden",
														0
													);
													dialog.set_df_property(
														field.fieldname,
														"reqd",
														0
													);
												} else {
													dialog.set_df_property(
														field.fieldname,
														"hidden",
														1
													);
													dialog.set_df_property(
														field.fieldname,
														"reqd",
														0
													);
												}
											});
										} else {
											task.fields_to_display.forEach((field) => {
												if (field.hidden === 0) {
													dialog.set_df_property(
														field.fieldname,
														"hidden",
														0
													);
												}
												if (
													[
														"due_date",
														"exp_end_date",
														"reschedule_remarks",
													].includes(field.fieldname)
												) {
													dialog.set_df_property(
														field.fieldname,
														"hidden",
														1
													);
													dialog.set_df_property(
														field.fieldname,
														"reqd",
														0
													);
												}
												if (field.reqd) {
													dialog.set_df_property(
														field.fieldname,
														"reqd",
														field.reqd
													);
												}
											});
										}
									},
								},
								...dialog_fields,
							],
							primary_action_label: "Update",
							primary_action(values) {
								frappe.call({
									method: "checklist.checklist.page.task_list.task_list.update_task",
									args: {
										name: task.name,
										updates: values,
									},
									callback: function (response) {
										if (response.message === "success") {
											frappe.msgprint("Task updated successfully.");
											load_tasks(false);
										} else {
											frappe.msgprint("Failed to update task.");
										}
									},
								});
								dialog.hide();
							},
						});

						task.fields_to_display.forEach((field) => {
							if (field.fieldname !== "status") {
								dialog.set_df_property(field.fieldname, "hidden", 1);
							}
						});

						dialog.show();
					}
				});

				// View button handler
				$viewBtn.on("click", function () {
					frappe.set_route("Form", "Task", task.name);
				});

				$row.appendTo($tbody);
			});
		} else if (!append) {
			let colSpan = frappe.user_roles.includes("Checklist Admin") ? 6 : 5;
			$tbody.append(
				`<tr><td colspan="${colSpan}" class="text-center">No tasks found</td></tr>`
			);
			$("#show-more-container").hide();
		}
	}

	// -------------------- Show More button --------------------
	$("#show-more-btn").on("click", function () {
		if (hasMoreTasks && !isLoading) {
			currentPage++; // increment only here
			load_tasks(true);
		}
	});

	// Initial load
	load_tasks(false);

	// Filter change handlers
	$("#filter-start-date, #filter-end-date, #filter-status, #filter-user").on(
		"change",
		function () {
			load_tasks(false);
		}
	);
};
