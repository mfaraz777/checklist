// // Copyright (c) 2025, Avi Root Info Solutions and contributors
// // For license information, please see license.txt

function openRepeatDialog(frm) {
    let repeat_every_options = Array.from({ length: 99 }, (_, i) => (i + 1).toString());

    const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

    let repeat_dialog = new frappe.ui.Dialog({
        title: 'Recurring Task Settings',
        fields: [
                {
                    label: 'Start Date',
                    fieldname: 'start_date',
                    fieldtype: 'Date',
                    default: frappe.datetime.get_today(),
                    onchange: () => updateWeekdayButtons()

                },
                {
                    label: 'Repeat every',
                    fieldname: 'repeat_interval',
                    fieldtype: 'Select',
                    options: repeat_every_options,
                    default: '1',
                    onchange: () => {
                        updateWeekdayButtons();
                    }
                },
                {
                    label: 'Interval Unit',
                    fieldname: 'interval_unit',
                    fieldtype: 'Select',
                    options: ['day', 'week', 'month', 'year'],
                    default: 'day',
                    onchange: () => updateWeekdayButtons()
                },
                {
                    fieldname: 'monthly_options',
                    fieldtype: 'HTML',
                    options: `
                        <div id="monthly-options" style="margin-top: 10px; display: none;">
                            <label style="display: block; margin-bottom: 5px;"><strong>Repeat On:</strong></label>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="monthly_repeat_type" value="today" checked> On day <span id="monthly-day-num">20</span>
                            </div>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="monthly_repeat_type" value="fourth"> On the fourth <span id="monthly-weekday"></span>
                            </div>
                        </div>
                    `
                },
                {
                    fieldname: 'yearly_options',
                    fieldtype: 'HTML',
                    options: `
                        <div id="yearly-options" style="margin-top: 10px; display: none;">
                            <label style="display: block; margin-bottom: 5px;"><strong>Repeat On:</strong></label>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="yearly_repeat_type" value="date" checked> On <span id="yearly-month-day">20</span>
                            </div>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="yearly_repeat_type" value="fourth"> On the fourth <span id="yearly-weekday"></span>
                            </div>
                        </div>
                    `
                },

                {
                    fieldname: 'repeat_days_html',
                    fieldtype: 'HTML',
                    label: 'Repeat on',
                    options: `
                        <div id="weekday-buttons" style="
                            display: flex;
                            flex-wrap: nowrap;
                            gap: 6px;
                            margin-bottom: 15px;
                            margin-top: 6px;
                            align-items: center;
                        ">
                            ${dayLabels.map((d, i) => 
                                `<button type="button" class="weekday-btn" data-day="${i}" style="
                                    padding: 6px 10px;
                                    border: none;
                                    border-radius: 50%;
                                    background-color: #f3f3f3;
                                    cursor: pointer;
                                    font-weight: bold;
                                    width: 32px;
                                    height: 32px;
                                    transition: 0.2s;
                                ">${d}</button>`).join(' ')
                        }</div>
                        <input type="hidden" id="selected-days" />
                    `
                },
                {
                    label: 'End Date',
                    fieldname: 'end_date',
                    fieldtype: 'Date',
                    description: 'Leave blank for no end date'
                }
            ],
            primary_action_label: 'Save',
            primary_action(values) {
                if (values.interval_unit === 'month' || values.interval_unit === 'months') {
                    const selected = document.querySelector('input[name="monthly_repeat_type"]:checked');
                    const startDate = frappe.datetime.str_to_obj(values.start_date);
                    const weekdayInfo = getWeekdayOccurrenceFor(startDate);
                    console.log('Weekday Info:', weekdayInfo);

                    if (selected) {
                        if (selected.value === 'today') {
                            values.monthly_repeat_type = {
                                type: 'date',
                                day: startDate.getDate()
                            };
                        } else {
                            values.monthly_repeat_type = {
                                type: selected.value,
                                weekday: weekdayInfo.weekday,
                                occurrence: weekdayInfo.occurrence
                            };
                        }
                    }
                }

                if (values.interval_unit === 'year') {
                    const selected = document.querySelector('input[name="yearly_repeat_type"]:checked');
                    const startDate = frappe.datetime.str_to_obj(values.start_date);
                    const weekdayInfo = getWeekdayOccurrenceFor(startDate);
                    const monthName = startDate.toLocaleString('default', { month: 'long' });

                    if (selected) {
                        if (selected.value === 'date') {
                            values.yearly_repeat_type = {
                                type: 'date',
                                day: startDate.getDate(),
                                month: monthName
                            };
                        } else {
                            values.yearly_repeat_type = {
                                type: selected.value,
                                weekday: weekdayInfo.weekday,
                                occurrence: weekdayInfo.occurrence,
                                month: monthName
                            };
                        }
                    }
                }
                const selected = [...document.querySelectorAll('.weekday-btn.active')]
                    .map(btn => parseInt(btn.dataset.day));

                console.log(selected, "selected")

                values.repeat_days = selected;

                console.log('Values:', values);

                frm.set_value('start_date', values.start_date);
                frm.set_value('end_date', values.end_date);
                frm.set_value('repeat_interval', values.repeat_interval);
                frm.set_value('interval_unit', values.interval_unit);
                frm.set_value('repeat_days', JSON.stringify(values.repeat_days));
                frm.set_value('month_repeat_type', JSON.stringify(values.monthly_repeat_type));
                frm.set_value('year_repeat_type', JSON.stringify(values.yearly_repeat_type));

                frappe.msgprint(__('Recurring settings saved successfully'));
                repeat_dialog.hide();
                frm.reload_doc();

                // frappe.call({
                //     method: 'checklist.checklist.doctype.master_tasks.master_tasks.save_recurring_settings',
                //     args: {
                //         docname: frm.doc.name,
                //         data: JSON.stringify(values)
                //     },
                //     callback: function (r) {
                //         if (!r.exc) {
                //             frappe.msgprint(__('Recurring settings saved successfully'));
                //             repeat_dialog.hide();
                //             frm.reload_doc();
                //         } else {
                //             frappe.msgprint(__('Failed to save recurring settings.'));
                //         }
                //     }
                // });
            }

        });

        repeat_dialog.show();

        // Enable weekday toggle
        setTimeout(() => {
            setupWeekdayToggle();
            updateWeekdayButtons();
        }, 200);

        // function updateIntervalUnitOptions() {
        //     const repeatEvery = parseInt(repeat_dialog.get_value('repeat_interval'), 10);

        //     const singularUnits = ['day', 'week', 'month', 'year'];
        //     const pluralUnits = ['days', 'weeks', 'months', 'years'];

        //     const unitField = repeat_dialog.fields_dict.interval_unit;
        //     const currentValue = repeat_dialog.get_value('interval_unit');
        //     const options = repeatEvery > 1 ? pluralUnits : singularUnits;

        //     // Set updated options
        //     unitField.df.options = options;
        //     unitField.refresh();

        //     // Retain previously selected value if still valid, otherwise reset to default
        //     if (!options.includes(currentValue)) {
        //         repeat_dialog.set_value('interval_unit', options[0]);
        //     }
        // }

        function setupWeekdayToggle() {
            const buttons = document.querySelectorAll('.weekday-btn');
            buttons.forEach(btn => {
                btn.addEventListener('click', () => {
                    btn.classList.toggle('active');
                    btn.style.backgroundColor = btn.classList.contains('active') ? '#007bff' : '#f3f3f3';
                    btn.style.color = btn.classList.contains('active') ? '#fff' : '#000';
                });
            });
        }

        function getWeekdayOccurrence(date) {
            const day = date.getDay();
            const dateOfMonth = date.getDate();

            // Count how many times this weekday has occurred in the month until this date
            let count = 0;
            for (let i = 1; i <= dateOfMonth; i++) {
                const tempDate = new Date(date.getFullYear(), date.getMonth(), i);
                if (tempDate.getDay() === day) {
                    count++;
                }
            }

            // Check if it's the last occurrence of the weekday in the month
            const nextWeekSameDay = new Date(date);
            nextWeekSameDay.setDate(date.getDate() + 7);
            const isLast = nextWeekSameDay.getMonth() !== date.getMonth();

            return {
                count,
                isLast
            };
        }

        function getWeekdayOccurrenceFor(date) {
            const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const day = date.getDay(); // 0-6 (Sunday to Saturday)
            const dateNum = date.getDate();

            const weekOfMonth = Math.floor((dateNum - 1) / 7); // 0 = first, 1 = second, etc.
            const lastDayOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0);

            const lastDayNum = lastDayOfMonth.getDate();
            const lastDayWeekOfMonth = Math.floor((lastDayNum - 1) / 7);
            // const isLast =
            //     date.getDay() === lastDayOfMonth.getDay() &&
            //     weekOfMonth === lastDayWeekOfMonth;
            const nextWeekSameDay = new Date(date);
            nextWeekSameDay.setDate(date.getDate() + 7);
            const isLast = nextWeekSameDay.getMonth() !== date.getMonth();
            

            return {
                weekday: weekdays[day],
                occurrence: isLast ? 'last' : ['first', 'second', 'third', 'fourth'][weekOfMonth]
            };
        }


        function updateWeekdayButtons() {
            const unit = repeat_dialog.get_value('interval_unit');
            const weekdayContainer = document.getElementById('weekday-buttons');
            const monthlyOptions = document.getElementById('monthly-options');
            const yearlyOptions = document.getElementById('yearly-options');
            const buttons = document.querySelectorAll('.weekday-btn');

            if (unit === 'day' || unit === 'days') {
                const repeatEvery = parseInt(repeat_dialog.get_value('repeat_interval'), 10);

                if (repeatEvery > 1) {
                    // Hide and clear weekdays
                    weekdayContainer.style.display = 'none';
                } else {
                    // Show and activate all weekdays
                    weekdayContainer.style.display = 'flex';
                    buttons.forEach(btn => {
                        btn.classList.add('active');
                        btn.style.backgroundColor = '#007bff';
                        btn.style.color = '#fff';
                    });
                }
                monthlyOptions.style.display = 'none';
                yearlyOptions.style.display = 'none';
            } else if (unit === 'week' || unit === 'weeks') {
                weekdayContainer.style.display = 'flex';
                monthlyOptions.style.display = 'none';
                yearlyOptions.style.display = 'none';
                const startDate = frappe.datetime.str_to_obj(repeat_dialog.get_value('start_date'));
                const todayIndex = (startDate.getDay() + 6) % 7;
                buttons.forEach((btn, i) => {
                    if (i === todayIndex) {
                        btn.classList.add('active');
                        btn.style.backgroundColor = '#007bff';
                        btn.style.color = '#fff';
                    } else {
                        btn.classList.remove('active');
                        btn.style.backgroundColor = '#f3f3f3';
                        btn.style.color = '#000';
                    }
                });
            } else if (unit === 'month' || unit === 'months') {
                weekdayContainer.style.display = 'none';
                document.querySelectorAll('.weekday-btn').forEach(btn => {
                    btn.classList.remove('active');
                    btn.style.backgroundColor = '#f3f3f3';
                    btn.style.color = '#000';
                });

                monthlyOptions.style.display = 'block';
                yearlyOptions.style.display = 'none';

                // Populate dynamic day and weekday info
                const startDate = frappe.datetime.str_to_obj(repeat_dialog.get_value('start_date'));

                document.getElementById('monthly-day-num').innerText = startDate.getDate();

                const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                const weekdayName = weekdays[startDate.getDay()];
                const { count, isLast } = getWeekdayOccurrence(startDate);

                const ordinalMap = ['first', 'second', 'third', 'fourth', 'fifth'];
                const ordinal = isLast ? 'last' : ordinalMap[count - 1] || `${count}th`;

                document.querySelector('#monthly-options input[value="fourth"]').nextSibling.textContent = ` On the ${ordinal} ${weekdayName}`;

            } else if (unit === 'year' || unit === 'years') {
                yearlyOptions.style.display = 'block';
                monthlyOptions.style.display = 'none';
                weekdayContainer.style.display = 'none';
                document.querySelectorAll('.weekday-btn').forEach(btn => {
                    btn.classList.remove('active');
                    btn.style.backgroundColor = '#f3f3f3';
                    btn.style.color = '#000';
                });
                const startDate = frappe.datetime.str_to_obj(repeat_dialog.get_value('start_date'));

                // Format month and day
                const monthName = startDate.toLocaleString('default', { month: 'long' });
                const dateNum = startDate.getDate();
                document.getElementById('yearly-month-day').innerText = `${monthName} ${dateNum}`;

                // Format weekday
                const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                const weekday = weekdays[startDate.getDay()];
                const { count, isLast } = getWeekdayOccurrence(startDate);
                const ordinalMap = ['first', 'second', 'third', 'fourth', 'fifth'];
                const ordinal = isLast ? 'last' : ordinalMap[count - 1] || `${count}th`;

                document.querySelector('#yearly-options input[value="fourth"]').nextSibling.textContent = ` On the ${ordinal} ${weekday} of ${monthName}`;

            }else {
                console.log('Invalid interval unit');
                weekdayContainer.style.display = 'none';
                monthlyOptions.style.display = 'none';
                yearlyOptions.style.display = 'none';
            }
        }
    }

function editRepeatDialog(frm, options = {}) {
    console.log('Options:', options);
    let repeat_every_options = Array.from({ length: 99 }, (_, i) => (i + 1).toString());

    const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

    let repeat_dialog = new frappe.ui.Dialog({
        title: 'Recurring Task Settings',
        fields: [
                {
                    label: 'Start Date',
                    fieldname: 'start_date',
                    fieldtype: 'Date',
                    default: options.start_date || frappe.datetime.get_today(),
                    onchange: () => updateWeekdayButtons()

                },
                {
                    label: 'Repeat every',
                    fieldname: 'repeat_interval',
                    fieldtype: 'Select',
                    options: repeat_every_options,
                    default: options.repeat_interval || '1',
                    onchange: () => {
                        updateWeekdayButtons();
                    }
                },
                {
                    label: 'Interval Unit',
                    fieldname: 'interval_unit',
                    fieldtype: 'Select',
                    options: ['day', 'week', 'month', 'year'],
                    default: options.interval_unit || 'day',
                    onchange: () => updateWeekdayButtons()
                },
                {
                    fieldname: 'monthly_options',
                    fieldtype: 'HTML',
                    options: `
                        <div id="monthly-options" style="margin-top: 10px; display: none;">
                            <label style="display: block; margin-bottom: 5px;"><strong>Repeat On:</strong></label>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="monthly_repeat_type" value="today" checked> On day <span id="monthly-day-num">20</span>
                            </div>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="monthly_repeat_type" value="fourth"> On the fourth <span id="monthly-weekday"></span>
                            </div>
                        </div>
                    `
                },
                {
                    fieldname: 'yearly_options',
                    fieldtype: 'HTML',
                    options: `
                        <div id="yearly-options" style="margin-top: 10px; display: none;">
                            <label style="display: block; margin-bottom: 5px;"><strong>Repeat On:</strong></label>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="yearly_repeat_type" value="date" checked> On <span id="yearly-month-day">20</span>
                            </div>
                            <div style="margin-bottom: 6px;">
                                <input type="radio" name="yearly_repeat_type" value="fourth"> On the fourth <span id="yearly-weekday"></span>
                            </div>
                        </div>
                    `
                },

                {
                    fieldname: 'repeat_days_html',
                    fieldtype: 'HTML',
                    label: 'Repeat on',
                    options: `
                        <div id="weekday-buttons" style="
                            display: flex;
                            flex-wrap: nowrap;
                            gap: 6px;
                            margin-bottom: 15px;
                            margin-top: 6px;
                            align-items: center;
                        ">
                            ${dayLabels.map((d, i) => 
                                `<button type="button" class="weekday-btn" data-day="${i}" style="
                                    padding: 6px 10px;
                                    border: none;
                                    border-radius: 50%;
                                    background-color: #f3f3f3;
                                    cursor: pointer;
                                    font-weight: bold;
                                    width: 32px;
                                    height: 32px;
                                    transition: 0.2s;
                                ">${d}</button>`).join(' ')
                        }</div>
                        <input type="hidden" id="selected-days" />
                    `
                },
                {
                    label: 'End Date',
                    fieldname: 'end_date',
                    fieldtype: 'Date',
                    default: options.end_date || '',
                    description: 'Leave blank for no end date'
                }
            ],
            primary_action_label: 'Save',
            primary_action(values) {
                if (values.interval_unit === 'month' || values.interval_unit === 'months') {
                    const selected = document.querySelector('input[name="monthly_repeat_type"]:checked');
                    const startDate = frappe.datetime.str_to_obj(values.start_date);
                    const weekdayInfo = getWeekdayOccurrenceFor(startDate);
                    console.log('Weekday Info:', weekdayInfo);

                    if (selected) {
                        if (selected.value === 'today') {
                            values.monthly_repeat_type = {
                                type: 'date',
                                day: startDate.getDate()
                            };
                        } else {
                            values.monthly_repeat_type = {
                                type: selected.value,
                                weekday: weekdayInfo.weekday,
                                occurrence: weekdayInfo.occurrence
                            };
                        }
                    }
                }

                if (values.interval_unit === 'year') {
                    const selected = document.querySelector('input[name="yearly_repeat_type"]:checked');
                    const startDate = frappe.datetime.str_to_obj(values.start_date);
                    const weekdayInfo = getWeekdayOccurrenceFor(startDate);
                    const monthName = startDate.toLocaleString('default', { month: 'long' });

                    if (selected) {
                        if (selected.value === 'date') {
                            values.yearly_repeat_type = {
                                type: 'date',
                                day: startDate.getDate(),
                                month: monthName
                            };
                        } else {
                            values.yearly_repeat_type = {
                                type: selected.value,
                                weekday: weekdayInfo.weekday,
                                occurrence: weekdayInfo.occurrence,
                                month: monthName
                            };
                        }
                    }
                }
                const selected = [...document.querySelectorAll('.weekday-btn.active')]
                    .map(btn => parseInt(btn.dataset.day));
                
                console.log(selected, "selected")
                values.repeat_days = selected;

                frappe.call({
                    method: 'checklist.checklist.doctype.master_tasks.master_tasks.save_recurring_settings',
                    args: {
                        docname: frm.doc.name,
                        data: JSON.stringify(values)
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Recurring settings saved successfully'));
                            repeat_dialog.hide();
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to save recurring settings.'));
                        }
                    }
                });
            }

        });

        repeat_dialog.show();

        // Enable weekday toggle
        setTimeout(() => {
            if (options.start_date) repeat_dialog.set_value('start_date', options.start_date);
            if (options.end_date) repeat_dialog.set_value('end_date', options.end_date);
            if (options.repeat_interval) repeat_dialog.set_value('repeat_interval', options.repeat_interval);
            if (options.interval_unit) repeat_dialog.set_value('interval_unit', options.interval_unit);

            // Setup buttons
            const repeat_days = options.repeat_days || [];
            console.log('Repeat Days:', repeat_days);
            if (repeat_days.length > 0) {
                setupWeekdayToggle(repeat_days);
            }

            if (options.monthly_repeat_type){
                const optionMonthly = JSON.parse(options.monthly_repeat_type) || {};
                if (options.interval_unit === 'month') {
                    document.querySelector(`input[name="monthly_repeat_type"][value="${optionMonthly.type}"]`)?.click();
                }
            }
            if (options.yearly_repeat_type){
                const optionYearly = JSON.parse(options.yearly_repeat_type) || {};
                if (options.interval_unit === 'year') {
                    document.querySelector(`input[name="yearly_repeat_type"][value="${optionYearly.type}"]`)?.click();
                }

            }
        }, 300);

        function setupWeekdayToggle(selectedDays = []) {
            console.log('Selected Days:', selectedDays, typeof selectedDays);
            // Ensure selectedDays is always an array of numbers
            if (selectedDays.length === 0) {
                console.log('No selected days, setting up default buttons');
                const buttons = document.querySelectorAll('.weekday-btn');
                buttons.forEach(btn => {
                    btn.addEventListener('click', () => {
                        btn.classList.toggle('active');
                        btn.style.backgroundColor = btn.classList.contains('active') ? '#007bff' : '#f3f3f3';
                        btn.style.color = btn.classList.contains('active') ? '#fff' : '#000';
                    });
                });
            }
            let normalizedDays = [];

            if (Array.isArray(selectedDays)) {
                normalizedDays = selectedDays.map(d => parseInt(d));
            } else if (typeof selectedDays === 'object') {
                normalizedDays = Object.values(selectedDays).map(d => parseInt(d));
            }
            const buttons = document.querySelectorAll('.weekday-btn');
            buttons.forEach((btn) => {
                const day = parseInt(btn.dataset.day);

                // Pre-select if in normalized values
                if (normalizedDays.includes(day)) {
                    console.log('Button for day', day, 'is active');
                    document.getElementById('selected-days').value += day + ',';
                    btn.classList.add('active');
                    btn.style.backgroundColor = '#007bff';
                    btn.style.color = '#fff';
                } else {
                    console.log('Button for day', day, 'is inactive');
                    btn.classList.remove('active');
                    btn.style.backgroundColor = '#f3f3f3';
                    btn.style.color = '#000';
                }

                // Add toggle behavior
                btn.addEventListener('click', () => {
                    btn.classList.toggle('active');
                    btn.style.backgroundColor = btn.classList.contains('active') ? '#007bff' : '#f3f3f3';
                    btn.style.color = btn.classList.contains('active') ? '#fff' : '#000';
                });
            });
        }

        function getWeekdayOccurrence(date) {
            const day = date.getDay();
            const dateOfMonth = date.getDate();

            // Count how many times this weekday has occurred in the month until this date
            let count = 0;
            for (let i = 1; i <= dateOfMonth; i++) {
                const tempDate = new Date(date.getFullYear(), date.getMonth(), i);
                if (tempDate.getDay() === day) {
                    count++;
                }
            }

            // Check if it's the last occurrence of the weekday in the month
            const nextWeekSameDay = new Date(date);
            nextWeekSameDay.setDate(date.getDate() + 7);
            const isLast = nextWeekSameDay.getMonth() !== date.getMonth();

            return {
                count,
                isLast
            };
        }

        function getWeekdayOccurrenceFor(date) {
            const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const day = date.getDay(); // 0-6 (Sunday to Saturday)
            const dateNum = date.getDate();

            const weekOfMonth = Math.floor((dateNum - 1) / 7); // 0 = first, 1 = second, etc.
            const lastDayOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0);

            const lastDayNum = lastDayOfMonth.getDate();
            const lastDayWeekOfMonth = Math.floor((lastDayNum - 1) / 7);
            // const isLast =
            //     date.getDay() === lastDayOfMonth.getDay() &&
            //     weekOfMonth === lastDayWeekOfMonth;
            const nextWeekSameDay = new Date(date);
            nextWeekSameDay.setDate(date.getDate() + 7);
            const isLast = nextWeekSameDay.getMonth() !== date.getMonth();

            return {
                weekday: weekdays[day],
                occurrence: isLast ? 'last' : ['first', 'second', 'third', 'fourth'][weekOfMonth]
            };
        }

        function updateWeekdayButtons() {
            const unit = repeat_dialog.get_value('interval_unit');
            const weekdayContainer = document.getElementById('weekday-buttons');
            const monthlyOptions = document.getElementById('monthly-options');
            const yearlyOptions = document.getElementById('yearly-options');
            const buttons = document.querySelectorAll('.weekday-btn');

            if (unit === 'day' || unit === 'days') {
                const repeatEvery = parseInt(repeat_dialog.get_value('repeat_interval'), 10);

                if (repeatEvery > 1) {
                    // Hide and clear weekdays
                    weekdayContainer.style.display = 'none';
                }

                monthlyOptions.style.display = 'none';
                yearlyOptions.style.display = 'none';
            
            } else if (unit === 'week' || unit === 'weeks') {
                weekdayContainer.style.display = 'flex';
                monthlyOptions.style.display = 'none';
                yearlyOptions.style.display = 'none';
                const startDate = frappe.datetime.str_to_obj(repeat_dialog.get_value('start_date'));
                const todayIndex = (startDate.getDay() + 6) % 7;
                // buttons.forEach((btn, i) => {
                //     if (i === todayIndex) {
                //         btn.classList.add('active');
                //         btn.style.backgroundColor = '#007bff';
                //         btn.style.color = '#fff';
                //     } else {
                //         btn.classList.remove('active');
                //         btn.style.backgroundColor = '#f3f3f3';
                //         btn.style.color = '#000';
                //     }
                // });
            
            } else if (unit === 'month' || unit === 'months') {
                const monthData = options.monthly_repeat_type || {};
                weekdayContainer.style.display = 'none';
                document.querySelectorAll('.weekday-btn').forEach(btn => {
                    btn.classList.remove('active');
                    btn.style.backgroundColor = '#f3f3f3';
                    btn.style.color = '#000';
                });

                monthlyOptions.style.display = 'block';
                yearlyOptions.style.display = 'none';

                // Populate dynamic day and weekday info
                const startDate = frappe.datetime.str_to_obj(repeat_dialog.get_value('start_date'));

                document.getElementById('monthly-day-num').innerText = startDate.getDate();

                const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                const weekdayName = weekdays[startDate.getDay()];
                const { count, isLast } = getWeekdayOccurrence(startDate);

                const ordinalMap = ['first', 'second', 'third', 'fourth', 'fifth'];
                const ordinal = isLast ? 'last' : ordinalMap[count - 1] || `${count}th`;


                document.querySelector('#monthly-options input[value="fourth"]').nextSibling.textContent = ` On the ${ordinal} ${weekdayName}`;

            } else if (unit === 'year' || unit === 'years') {
                yearlyOptions.style.display = 'block';
                monthlyOptions.style.display = 'none';
                weekdayContainer.style.display = 'none';
                document.querySelectorAll('.weekday-btn').forEach(btn => {
                    btn.classList.remove('active');
                    btn.style.backgroundColor = '#f3f3f3';
                    btn.style.color = '#000';
                });
                const startDate = frappe.datetime.str_to_obj(repeat_dialog.get_value('start_date'));

                // Format month and day
                const monthName = startDate.toLocaleString('default', { month: 'long' });
                const dateNum = startDate.getDate();
                document.getElementById('yearly-month-day').innerText = `${monthName} ${dateNum}`;

                // Format weekday
                const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                const weekday = weekdays[startDate.getDay()];
                const { count, isLast } = getWeekdayOccurrence(startDate);
                const ordinalMap = ['first', 'second', 'third', 'fourth', 'fifth'];
                const ordinal = isLast ? 'last' : ordinalMap[count - 1] || `${count}th`;

                document.querySelector('#yearly-options input[value="fourth"]').nextSibling.textContent = ` On the ${ordinal} ${weekday} of ${monthName}`;

            }else {
                console.log('Invalid interval unit');
                weekdayContainer.style.display = 'none';
                monthlyOptions.style.display = 'none';
                yearlyOptions.style.display = 'none';
            }
        }
    }

frappe.ui.form.on('Master Tasks', {
     onload: function(frm) {
        if (!frm.doc.task_assigner) {
            frm.set_value('task_assigner', frappe.session.user);
        } 
        frm.fields_dict['assignee_doers'].grid.get_field('employee').get_query = function(doc, cdt, cdn) {
            return {
               query : 'checklist.api.user_with_employee_query',
            };
        };
        frm.set_query('project', function() {
            return {
                filters: [
                    ['name', 'not in', ['PROJ-0002', 'PROJ-0001']]
                ]
            };
        });
    },
    refresh: function (frm) {
        if (frm.doc.task_type === 'Recurring') {
            frm.add_custom_button(__('Update Recurring'), function () {
                const saved_data = {
                    start_date: frm.doc.start_date,
                    end_date: frm.doc.end_date,
                    repeat_interval: frm.doc.repeat_interval,
                    interval_unit: frm.doc.interval_unit,
                    repeat_days: JSON.parse(frm.doc.repeat_days || '[]'),
                    monthly_repeat_type: frm.doc.month_repeat_type,
                    yearly_repeat_type: frm.doc.year_repeat_type
                };
                editRepeatDialog(frm, saved_data);
            });
        }
    },
    task_type: function (frm) {
        if (frm.doc.task_type === 'Recurring') {
            openRepeatDialog(frm);
            // frm.add_custom_button(__('Edit Recurring'), function () {
            //     const saved_data = {
            //         start_date: frm.doc.start_date,
            //         end_date: frm.doc.end_date,
            //         repeat_interval: frm.doc.repeat_interval,
            //         interval_unit: frm.doc.interval_unit,
            //         repeat_days: JSON.parse(frm.doc.repeat_days || '[]'),
            //         monthly_repeat_type: frm.doc.monthly_repeat_type,
            //         yearly_repeat_type: frm.doc.yearly_repeat_type
            //     };
            //     editRepeatDialog(frm, saved_data);
            // });
        }
    }
});