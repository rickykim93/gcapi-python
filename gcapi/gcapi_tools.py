import re
from datetime import datetime


# Constants
SPAN_M = [1, 2, 3, 5, 10, 15, 30] # Span intervals for minutes
SPAN_H = [1, 2, 4, 8] # Span intervals for hours
INTERVAL = ['HOUR', 'MINUTE', 'DAY', 'WEEK', 'MONTH']


def format_date(row):
    """ Extracts the unix timestamp from the string and converts it to a datetime object, best if used with map
    :param row: row from a dataframe """
    row=str(row)
    unix = [int(s) for s in re.findall(r'-?\d+\.?\d*', row)]
    dt_object = datetime.fromtimestamp(unix[0]/1000)
    return(dt_object)


def check_span(interval, span):
    """ Checks if the span is correct for the specific interval
    :param interval: time interval, can be min, hour, day, week, month
    :param span: span of time, it can be 1, 2, 3, 5, etc,,"""
    if interval == 'HOUR':
        if span not in [SPAN_H, str(SPAN_H)]:
            span = 1
            return span
        else:
            return span
    elif interval == 'MINUTE':
        if span not in [SPAN_M, str(SPAN_M)]:
            span = 1
            return span
        else:
            return span
    else:
        span = 1
        return span


def check_interval(interval):
    """ Checks if the interval is one of the correct intervals
    :param interval: time interval, can be min, hour, day, week, month"""
    if interval not in INTERVAL:
        interval = 'HOUR'
        return interval
    else:
        return interval
