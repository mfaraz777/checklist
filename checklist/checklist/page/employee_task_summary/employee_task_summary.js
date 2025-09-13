const CHART_COLORS = {
	blue: "#1E90FF",
	green: "#50C878",
	red: "#FF5B61",
};

function getPresetRange(rangeType) {
	const today = frappe.datetime.str_to_obj(frappe.datetime.now_date());
	let from_date, to_date;

	if (rangeType === "previous_week") {
		const dayOfWeek = today.getDay();
		if (dayOfWeek === 0) {
			from_date = frappe.datetime.add_days(today, -13);
			to_date = frappe.datetime.add_days(today, -7);
		} else if (dayOfWeek === 1) {
			from_date = frappe.datetime.add_days(today, -7);
			to_date = frappe.datetime.add_days(today, -1);
		} else {
			from_date = frappe.datetime.add_days(today, -(dayOfWeek - 1 + 7));
			to_date = frappe.datetime.add_days(today, 7 - dayOfWeek - 7);
		}
	} else if (rangeType === "previous_month") {
		// Get current year and month (0-11)
		const year = today.getFullYear();
		const month = today.getMonth();

		// First day of previous month
		const firstDayPrevMonth = new Date(year, month - 1, 1);

		// Last day of previous month
		const lastDayPrevMonth = new Date(year, month, 0);

		// Convert to Frappe date strings
		from_date = frappe.datetime.obj_to_str(firstDayPrevMonth);
		to_date = frappe.datetime.obj_to_str(lastDayPrevMonth);

		console.log("Calculated Previous Month Range:", { from_date, to_date });
	}

	return {
		from: frappe.datetime.obj_to_str(from_date),
		to: frappe.datetime.obj_to_str(to_date),
	};
}

function toTitleCase(str) {
	return str.replace(/\w\S*/g, function (txt) {
		return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
	});
}

// Add debounce utility if not already available
if (!frappe.utils.debounce) {
	frappe.utils.debounce = function (fn, delay) {
		let timeout;
		return function () {
			const context = this;
			const args = arguments;
			clearTimeout(timeout);
			timeout = setTimeout(() => {
				fn.apply(context, args);
			}, delay);
		};
	};
}

frappe.pages["employee-task-summary"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Employee Task Summary",
		single_column: true,
	});

	const filter_section = $(`<div class="row filters mb-3">
	
	<div class="col-md-2" id="from_date_wrapper"></div>
	<div class="col-md-2" id="to_date_wrapper"></div>
	<div class="col-md-3" id="employee_wrapper"></div>
    <div class="col-md-2" id="date_range_wrapper"></div>
</div>`).appendTo(page.body);

	const card_container = $('<div class="row mt-4"></div>').appendTo(page.body);
	const chart_container = $('<div class="row mt-4"></div>').appendTo(page.body);

	const filters = {
		date_range: frappe.ui.form.make_control({
			parent: $("#date_range_wrapper"),
			df: {
				label: "Date Range",
				fieldname: "date_range",
				fieldtype: "Select",
				options: ["Previous Week", "Previous Month", "Custom Range"],
				default: "Previous Week",
			},
		}),
		from_date: frappe.ui.form.make_control({
			parent: $("#from_date_wrapper"),
			df: {
				label: "From Date",
				fieldname: "from_date",
				fieldtype: "Date",
				default: getPresetRange("previous_week").from,
			},
		}),
		to_date: frappe.ui.form.make_control({
			parent: $("#to_date_wrapper"),
			df: {
				label: "To Date",
				fieldname: "to_date",
				fieldtype: "Date",
				default: getPresetRange("previous_week").to,
			},
		}),
		user: frappe.ui.form.make_control({
			parent: $("#employee_wrapper"),
			df: {
				label: "User",
				fieldname: "user",
				fieldtype: "Link",
				options: "User",
			},
		}),
	};

	Promise.all(
		Object.entries(filters).map(([key, ctrl]) => {
			return new Promise((resolve) => {
				ctrl.make();
				ctrl.refresh();
				if (key === "from_date") {
					ctrl.set_value(getPresetRange("previous_week").from);
				}
				if (key === "to_date") {
					ctrl.set_value(getPresetRange("previous_week").to);
				}
				resolve();
			});
		})
	).then(() => {
		// Initial refresh
		refresh_dashboard(filters, card_container, chart_container);

		// Create debounced refresh function
		const debouncedRefresh = frappe.utils.debounce(() => {
			refresh_dashboard(filters, card_container, chart_container);
		}, 500);

		// Set up event handlers for each control
		// Date fields
		filters.from_date.df.onchange = debouncedRefresh;
		filters.to_date.df.onchange = debouncedRefresh;

		// Link field
		filters.user.df.onchange = debouncedRefresh;
		filters.date_range.df.onchange = debouncedRefresh;

		// Add input/change events as fallback
		Object.values(filters).forEach((ctrl) => {
			ctrl.$input.on("input change", debouncedRefresh);
		});

		// Add Enter key support
		Object.values(filters).forEach((ctrl) => {
			ctrl.$input.on("keypress", function (e) {
				if (e.which === 13) {
					debouncedRefresh();
				}
			});
		});

		filters.date_range.$input.on("change", function () {
			const selected = filters.date_range.get_value().toLowerCase().replace(/\s/g, "_");

			if (selected === "custom_range") return;

			const range = getPresetRange(selected);
			filters.from_date.set_value(range.from);
			filters.to_date.set_value(range.to);
		});
		filters.date_range.set_value("Previous Week");
	});
};

function refresh_dashboard(filters, card_container, chart_container) {
	console.log("Refreshing dashboard");
	const from_date = filters.from_date.get_value();
	const to_date = filters.to_date.get_value();
	const user = filters.user.get_value();

	if (from_date && to_date) {
		frappe.call({
			method: "checklist.checklist.page.employee_task_summary.employee_task_summary.get_dashboard_data",
			args: { from_date, to_date, user },
			callback: function (r) {
				console.log("Dashboard data:", r.message);
				const data = r.message;
				card_container.empty();
				chart_container.empty();

				// 🧮 Render task summary table
				const stats = data.task_type_stats;

				if (stats) {
					const column_labels = [
						"Total Planned",
						"Total Actual",
						"% Work Done(KPI)",
						"% Work not done",
						"Work on time",
						"% Work not on time",
						"% Work on time",
					];

					let table_html = `
                    <div class="col-12 mb-4">
                        <div class="card p-3 shadow-sm">
                            <h5 class="mb-3">Task Summary by Type</h5>
                            <div class="table-responsive">
                                <table class="table table-bordered">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Task Type</th>
                                            ${column_labels
												.map((status) => `<th>${toTitleCase(status)}</th>`)
												.join("")}
                                        </tr>
                                    </thead>
                                    <tbody>
                `;

					Object.entries(stats).forEach(([task_type, values]) => {
						table_html += `<tr><td>${toTitleCase(task_type)}</td>`;
						column_labels.forEach((status) => {
							table_html += `<td>${values[status] || 0}</td>`;
						});
						table_html += `</tr>`;
					});

					table_html += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `;

					card_container.append(table_html);
				}

				card_container.append(`
					<div class="col-12 mb-4">
						<h4 class="text-center" style="margin-top: 20px; margin-bottom: 20px; color: #2e3c4a;">
							<i class="fa fa-lightbulb-o"></i> Overall Task Insights
						</h4>
					</div>
				`);

				// 🔢 Number Cards
				if (data.cards) {
					Object.entries(data.cards).forEach(([key, value]) => {
						const card_html = `
                        <div class="col-md-3">
                            <div class="card number-card text-center p-3 mb-3 shadow-sm">
                                <h3>${value}</h3>
                                <small class="text-muted">${toTitleCase(
									key.replace(/_/g, " ")
								)}</small>
                            </div>
                        </div>`;
						card_container.append(card_html);
					});
				}

				// Charts container
				chart_container.append(`
                <div class="col-12" id="chart-row">
                    <div class="row mb-4" id="bar-chart-row">
                        <div class="col-12">
                            <div id="bar-chart-wrapper">
                                <div class="chart task-white-bar" id="bar-chart" style="min-height: 300px;"></div>
                            </div>
                        </div>
                    </div>
                    <div class="row" id="pie-chart-row">
                        <div class="col-md-6 mb-4">
                            <div class="chart" id="pie-chart-1" style="min-height: 300px;"></div>
                        </div>
                        <div class="col-md-6 mb-4">
                            <div class="chart" id="pie-chart-2" style="min-height: 300px;"></div>
                        </div>
                    </div>
                </div>
            `);

				const chart_row = $("#chart-row");
				const chart_data = data.charts;
				const barChartEl = chart_row.find("#bar-chart")[0];

				// Render charts with requestAnimationFrame for better performance
				requestAnimationFrame(() => {
					// Bar Chart
					if (barChartEl && chart_data && chart_data.data) {
						new frappe.Chart(barChartEl, {
							title: chart_data.title || "Chart",
							data: chart_data.data,
							type: "bar",
							height: 300,
							horizontalBars: true,
							barOptions: {
								stacked: false,
								spaceRatio: 0.7,
							},
							valuesOverPoints: 1,
							colors: [CHART_COLORS.blue, CHART_COLORS.red],
						});
					}

					// Pie Charts
					const pie_charts = data.pi_charts;
					if (pie_charts && pie_charts.length >= 2) {
						// Pie Chart 1
						// Enhanced Pie Chart Configuration
						function createPieChart(selector, chartData, title) {
							// Ensure zeros are properly formatted in data
							const formattedData = {
								labels: chartData.labels,
								datasets: [
									{
										values: chartData.datasets[0].values.map((v) =>
											v === 0 ? 0.0001 : v
										),
									},
								],
							};

							return new frappe.Chart(selector, {
								title: title,
								data: formattedData,
								type: "pie",
								height: 300,
								is_navigable: true,
								valuesOverPoints: 1,
								formatTooltipY: (d) => {
									// Display actual zero for values we forced to 0.0001
									return d === 0.0001 ? "0" : d.toString();
								},
								tooltipOptions: {
									formatTooltipY: (d) => (d === 0.0001 ? "0" : d.toString()),
								},
								colors: [CHART_COLORS.green, CHART_COLORS.red],
							});
						}

						// Create your charts with this function
						createPieChart(
							"#pie-chart-1",
							pie_charts[0].data,
							pie_charts[0].title || "Pie Chart 1"
						);
						createPieChart(
							"#pie-chart-2",
							pie_charts[1].data,
							pie_charts[1].title || "Pie Chart 2"
						);
					}
				});
			},
			error: function (err) {
				console.error("Error loading dashboard data:", err);
				frappe.msgprint(__("Error loading dashboard data. Please try again."));
			},
		});
	} else {
		card_container.empty();
		chart_container.empty();
	}
}
