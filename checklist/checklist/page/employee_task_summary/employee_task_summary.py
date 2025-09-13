import frappe


@frappe.whitelist()
def safe_divide(numerator, denominator):
    return (numerator / denominator) if denominator else 0


@frappe.whitelist()
def get_dashboard_data(from_date, to_date, user=None):
    return {
        "task_type_stats": get_task_type_stats(from_date, to_date, user),
        "cards": get_task_cards(from_date, to_date, user),
        "charts": get_task_charts(from_date, to_date, user),
        "pi_charts": get_task_pi_charts(from_date, to_date, user),
    }


def get_task_type_stats(from_date, to_date, user=None):

    task_type = "One-Time"

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, params)

    count_of_all_one_time_tasks = result[0][0]

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, params)

    count_of_all_completed_one_time_tasks = result[0][0]

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
        "task.completed_on <= task.exp_end_date",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, params)

    count_of_one_time_tasks_completed_on_time = result[0][0]
    count_of_one_time_tasks_not_completed_on_time = (
        count_of_all_completed_one_time_tasks
        - count_of_one_time_tasks_completed_on_time
    )

    percent_of_not_completed_one_time_task = (
        safe_divide(
            count_of_all_one_time_tasks - count_of_all_completed_one_time_tasks,
            count_of_all_one_time_tasks,
        )
        * 100
    )

    if count_of_all_one_time_tasks == 0:
        percent_of_completed_one_time_task = 0
    else:
        percent_of_completed_one_time_task = (
            100 - percent_of_not_completed_one_time_task
        )

    percent_of_one_time_tasks_not_completed_on_time = (
        safe_divide(
            count_of_all_completed_one_time_tasks
            - count_of_one_time_tasks_completed_on_time,
            count_of_all_completed_one_time_tasks,
        )
        * 100
    )

    if count_of_all_completed_one_time_tasks == 0:
        percent_of_one_time_tasks_completed_on_time = 0
    else:
        percent_of_one_time_tasks_completed_on_time = (
            100 - percent_of_one_time_tasks_not_completed_on_time
        )

    task_type = "Recurring"

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, params)

    count_of_all_recurring_tasks = result[0][0]

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, params)

    count_of_all_completed_recurring_tasks = result[0][0]

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
        "task.completed_on <= task.exp_end_date",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, params)

    count_of_recurring_tasks_completed_on_time = result[0][0]
    count_of_recurring_tasks_not_completed_on_time = (
        count_of_all_completed_recurring_tasks
        - count_of_recurring_tasks_completed_on_time
    )

    percent_of_not_completed_recurring_task = (
        safe_divide(
            count_of_all_recurring_tasks - count_of_all_completed_recurring_tasks,
            count_of_all_recurring_tasks,
        )
        * 100
    )
    if count_of_all_recurring_tasks == 0:
        percent_of_completed_recurring_task = 0
    else:
        percent_of_completed_recurring_task = (
            100 - percent_of_not_completed_recurring_task
        )
    percent_of_recurring_tasks_not_completed_on_time = (
        safe_divide(
            count_of_all_completed_recurring_tasks
            - count_of_recurring_tasks_completed_on_time,
            count_of_all_completed_recurring_tasks,
        )
        * 100
    )
    if count_of_all_completed_recurring_tasks == 0:
        percent_of_recurring_tasks_completed_on_time = 0
    else:
        percent_of_recurring_tasks_completed_on_time = (
            100 - percent_of_recurring_tasks_not_completed_on_time
        )

    return {
        "Delegation": {
            "Total Planned": count_of_all_one_time_tasks,
            "Total Actual": count_of_all_completed_one_time_tasks,
            "% Work Done(KPI)": round(percent_of_completed_one_time_task, 2),
            "% Work not done": round(percent_of_not_completed_one_time_task, 2),
            "Work on time": round(count_of_one_time_tasks_completed_on_time, 2),
            "% Work not on time": round(
                percent_of_one_time_tasks_not_completed_on_time, 2
            ),
            "% Work on time": round(percent_of_one_time_tasks_completed_on_time, 2),
        },
        "Checklist": {
            "Total Planned": round(count_of_all_recurring_tasks, 2),
            "Total Actual": round(count_of_all_completed_recurring_tasks, 2),
            "% Work Done(KPI)": round(percent_of_completed_recurring_task, 2),
            "% Work not done": round(percent_of_not_completed_recurring_task, 2),
            "Work on time": round(count_of_recurring_tasks_completed_on_time, 2),
            "% Work not on time": round(
                percent_of_recurring_tasks_not_completed_on_time, 2
            ),
            "% Work on time": round(percent_of_recurring_tasks_completed_on_time, 2),
        },
    }


def get_task_cards(from_date, to_date, user=None):

    conditions = [
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
    ]
    params = [to_date, from_date]

    if user:
        conditions.insert(0, "task.custom_assigneedoer = %s")
        params.insert(0, user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_planned = frappe.db.sql(query, params)[0][0]

    conditions = [
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
    ]
    params = [to_date, from_date]

    if user:
        conditions.insert(0, "task.custom_assigneedoer = %s")
        params.insert(0, user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_completed = frappe.db.sql(query, params)[0][0]

    conditions = [
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
        "task.completed_on <= task.exp_end_date",
    ]
    params = [to_date, from_date]

    if user:
        conditions.insert(0, "task.custom_assigneedoer = %s")
        params.insert(0, user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_completed_on_time = frappe.db.sql(query, params)[0][0]

    percent_work_not_done = (
        safe_divide(total_planned - total_completed, total_planned) * 100
    )
    percent_work_done = 0
    if total_planned:
        percent_work_done = 100 - percent_work_not_done

    percent_work_not_done_on_time = (
        safe_divide(total_completed - total_completed_on_time, total_completed) * 100
    )
    percent_work_done_on_time = 0
    if total_completed:
        percent_work_done_on_time = 100 - percent_work_not_done_on_time

    return {
        "total_planned": total_planned,
        "total_actual": total_completed,
        "work_on_time": total_completed_on_time,
        "work_not_on_time": total_completed - total_completed_on_time,
        "%_work_done": round(percent_work_done, 2),
        "%_work_not_done": round(percent_work_not_done, 2),
        "%_work_on_time": round(percent_work_done_on_time, 2),
        "%_work_not_on_time": round(percent_work_not_done_on_time, 2),
    }


def get_task_charts(from_date, to_date, user=None):

    task_type = "One-Time"

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_one_time_task = frappe.db.sql(query, params)[0][0]

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'COMPLETED'",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_one_time_task_completed = frappe.db.sql(query, params)[0][0]

    task_type = "Recurring"

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_recurring_tasks = frappe.db.sql(query, params)[0][0]

    conditions = [
        "master.task_type = %s",
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'COMPLETED'",
    ]
    params = [task_type, to_date, from_date]

    if user:
        conditions.append("task.custom_assigneedoer = %s")
        params.append(user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_recurring_task_completed = frappe.db.sql(query, params)[0][0]

    chart_data = {
        "title": "Planned vs Actual Tasks",
        "data": {
            "labels": ["Delegation", "Checklist"],
            "datasets": [
                {
                    "name": "Total Planned",
                    "values": [
                        total_one_time_task,
                        total_recurring_tasks,
                    ],
                },
                {
                    "name": "Total Actual",
                    "values": [
                        total_one_time_task_completed,
                        total_recurring_task_completed,
                    ],
                },
            ],
        },
    }

    return chart_data


def get_task_pi_charts(from_date, to_date, user=None):

    conditions = ["task.exp_start_date <= %s", "task.exp_end_date >= %s"]
    params = [to_date, from_date]

    if user:
        conditions.insert(0, "task.custom_assigneedoer = %s")
        params.insert(0, user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_planned = frappe.db.sql(query, params)[0][0] or 0

    conditions = [
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
    ]
    params = [to_date, from_date]

    if user:
        conditions.insert(0, "task.custom_assigneedoer = %s")
        params.insert(0, user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_completed = frappe.db.sql(query, params)[0][0] or 0

    total_not_completed = total_planned - total_completed

    conditions = [
        "task.exp_start_date <= %s",
        "task.exp_end_date >= %s",
        "task.status = 'Completed'",
        "task.completed_on <= task.exp_end_date",
    ]
    params = [to_date, from_date]

    if user:
        conditions.insert(0, "task.custom_assigneedoer = %s")
        params.insert(0, user)

    query = f"""
        SELECT COUNT(*)
        FROM `tabTask` task
        JOIN `tabMaster Tasks` master ON task.custom_master_task = master.name
        WHERE {' AND '.join(conditions)}
    """

    total_completed_tasks_on_time = frappe.db.sql(query, params)[0][0] or 0

    total_completed_task_not_on_time = total_completed - total_completed_tasks_on_time

    return [
        {
            "title": "Total Tasks Summary",
            "data": {
                "labels": ["Completed", "Not Completed"],
                "datasets": [
                    {
                        "values": [
                            total_completed,
                            total_not_completed,
                        ]
                    }
                ],
            },
        },
        {
            "title": "Total Completed Tasks Summary",
            "data": {
                "labels": ["On Time", "Delayed"],
                "datasets": [
                    {
                        "values": [
                            total_completed_tasks_on_time,
                            total_completed_task_not_on_time,
                        ]
                    }
                ],
            },
        },
    ]
