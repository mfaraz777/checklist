from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU
import json
import frappe

WEEKDAY_MAP = {
    0: MO,
    1: TU,
    2: WE,
    3: TH,
    4: FR,
    5: SA,
    6: SU,
}

def parse_recurrence_input(input_data):
    weekday_map = {
        'monday': MO,
        'tuesday': TU,
        'wednesday': WE,
        'thursday': TH,
        'friday': FR,
        'saturday': SA,
        'sunday': SU
    }

    ordinal_map = {
        'first': 1,
        'second': 2,
        'third': 3,
        'fourth': 4,
        'last': -1
    }

    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }

    print("Parsing recurrence input:", input_data, type(input_data))

    weekday_str = input_data.get('weekday', '').lower()
    occurrence_str = input_data.get('occurrence', '').lower()
    month_str = input_data.get('month', '').lower()

    # Get weekday with occurrence (e.g., WE(2)) {'type': 'date', 'day': 28, 'month': 'May'}
    if weekday_str in weekday_map and occurrence_str in ordinal_map:
        byweekday = weekday_map[weekday_str](ordinal_map[occurrence_str])
    else:
        byweekday = None

    # Get month number
    if month_str in month_map:
        bymonth = month_map[month_str]
    else:
        bymonth = None

    return {
        'byweekday': byweekday,
        'bymonth': bymonth
    }

def generate_recurrences(
    start_datetime: datetime,
    recurrence_type: str,       # 'daily', 'weekly', 'monthly', 'yearly'
    interval: int = 1,
    count: int = None,
    until: datetime = None,
    weekdays: list = None,       # ['monday', 'thursday'] etc.
    data: dict = None
):
    recurrence_type = recurrence_type.lower()
    if recurrence_type not in ['day', 'week', 'month', 'year']:
        raise ValueError("Unsupported recurrence type")

    freq_map = {
        'day': DAILY,
        'week': WEEKLY,
        'month': MONTHLY,
        'year': YEARLY
    }

    freq = freq_map[recurrence_type]
    
    byweekday = None
    result = parse_recurrence_input(json.loads(data)) if data else {}
    print("Parsed recurrence data:", result)
    bymonth = result.get('bymonth', None)
    if recurrence_type in ['week', 'day'] and weekdays:
        byweekday = [WEEKDAY_MAP[day] for day in weekdays]
    elif recurrence_type in ['month', 'year']:
        if result.get('byweekday'):
            byweekday = [result['byweekday']]


    print(freq, interval, start_datetime, count, until, byweekday, bymonth)

    if until:
        rule = rrule(
            freq=freq,
            interval=interval,
            dtstart=start_datetime,
            until=until,
            byweekday=byweekday,
            bymonth=bymonth
        )
    else:
        rule = rrule(
            freq=freq,
            interval=interval,
            dtstart=start_datetime,
            count=count,
            byweekday=byweekday,
            bymonth=bymonth
        )

    return list(rule)
