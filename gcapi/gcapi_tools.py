import re
from datetime import datetime, timezone
from typing import Any


# Constants
SPAN_M = [1, 2, 3, 5, 10, 15, 30] # Span intervals for minutes
SPAN_H = [1, 2, 4, 8] # Span intervals for hours
INTERVAL = ['HOUR', 'MINUTE', 'DAY', 'WEEK', 'MONTH']


def format_date(row: Any) -> datetime:
    """ Extracts the unix timestamp (ms) from an API date string such as "/Date(1678406400000)/" and converts
    it to a timezone-aware UTC datetime, best if used with map
    :param row: row from a dataframe
    :return: datetime with tzinfo=timezone.utc """
    row=str(row)
    unix = [int(s) for s in re.findall(r'-?\d+\.?\d*', row)]
    dt_object = datetime.fromtimestamp(unix[0]/1000, tz=timezone.utc)
    return(dt_object)


def check_span(interval: str, span: Any) -> int:
    """ Checks if the span is correct for the specific interval
    :param interval: time interval, can be min, hour, day, week, month
    :param span: span of time, it can be 1, 2, 3, 5, etc. (int or numeric string)
    :return: span as an int if valid for the interval, otherwise 1"""
    if interval == 'HOUR':
        valid = SPAN_H
    elif interval == 'MINUTE':
        valid = SPAN_M
    else:
        return 1
    try:
        span = int(str(span))  # via str so 2.5 is rejected, not truncated to 2
    except (TypeError, ValueError):
        return 1
    return span if span in valid else 1


def check_interval(interval: str) -> str:
    """ Checks if the interval is one of the correct intervals
    :param interval: time interval, can be min, hour, day, week, month"""
    if interval not in INTERVAL:
        interval = 'HOUR'
        return interval
    else:
        return interval
