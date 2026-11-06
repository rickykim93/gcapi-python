"""Technical indicators (RSI, EMA, pivot points) built on GCapiClient price data.

All dates are timezone-aware: API dates are parsed with gcapi's ``format_date`` (UTC), and
timestamps sent to the API are Unix seconds computed from aware datetimes.

Usage::

    from gcapi import GCapiClient
    from technical_indicators import calc_hourly_rsi, calc_pivot

    api = GCapiClient(username="...", password="...", appkey="...")
    api.get_account_info()
    market_id = api.get_market_info("EUR/USD", get="MarketId")
    print(calc_hourly_rsi(api, market_id))
    print(calc_pivot(api, market_id))
"""

import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from gcapi.gcapi_tools import format_date

# FX trading days roll over at 17:00 New York time
ROLLOVER_TZ = "America/New_York"
ROLLOVER_HOUR = 17


def to_unix(dt):
    """
    Converts a timezone-aware datetime to the Unix timestamp (seconds, UTC) the API expects
    :param dt: timezone-aware datetime
    :return: Unix timestamp in seconds
    """
    if dt.tzinfo is None:
        raise ValueError("Use a timezone-aware datetime (e.g. datetime.now(timezone.utc))")
    return int(dt.timestamp())


def calc_rsi(series, n=14):
    """
    Returns RSI value given series of prices
    :param series: series of prices
    :param n: number of periods to calculate the initial RSI value
    :return: RSI
    """
    delta = series.diff()
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0
    RolUp = dUp.rolling(n).mean()
    RolDown = dDown.rolling(n).mean().abs()
    RS = RolUp / RolDown
    rsi = 100.0 - (100.0 / (1.0 + RS))
    return rsi


def _sample_prices(api, market_id, count, step):
    """
    Walks back from the latest tick, taking the last tick before each `step` interval
    :return: list of prices, oldest first
    """
    prices = []
    tick_date = None
    for i in range(count):
        if i == 0:
            resp = api.get_prices(market_id, num_ticks=2)
        else:
            resp = api.get_prices(market_id, num_ticks=2, to_ts=to_unix(tick_date - step))
        tick = resp["PriceTicks"][-1]
        tick_date = format_date(tick["TickDate"])
        prices.append(float(tick["Price"]))
    return list(reversed(prices))


def calc_hourly_rsi(api, market_id, n=14):
    """
    Calculates hourly RSI
    :param api: GCapiClient
    :param market_id: market ID
    :param n: number of periods to calculate initial RSI value
    :return: RSI
    """
    prices = _sample_prices(api, market_id, n + 1, timedelta(hours=1))
    return calc_rsi(pd.Series(prices)).iloc[-1]


def calc_5m_ema(api, market_id):
    """
    Calculate 5 minute exponential moving average (EMA)
    :param api: GCapiClient
    :param market_id: market ID
    :return: 8, 13, 21 5-minute EMAs
    """
    prices = pd.Series(_sample_prices(api, market_id, 21 * 2 + 1, timedelta(minutes=5)))
    return (
        prices.ewm(span=8, adjust=False).mean().iloc[-1],
        prices.ewm(span=13, adjust=False).mean().iloc[-1],
        prices.ewm(span=21, adjust=False).mean().iloc[-1],
    )


def previous_session(now=None):
    """
    Start and end (aware datetimes) of the last completed FX trading day, 17:00 to 17:00 New York time
    :param now: aware datetime to measure from (defaults to the current time)
    """
    tz = ZoneInfo(ROLLOVER_TZ)
    now = datetime.now(tz) if now is None else now.astimezone(tz)

    def rollover(days_ago):
        return (now - timedelta(days=days_ago)).replace(hour=ROLLOVER_HOUR, minute=0, second=0, microsecond=0)

    if now.hour >= ROLLOVER_HOUR:
        if now.weekday() == 6:  # sunday evening: last session was thursday -> friday
            return rollover(3), rollover(2)
        return rollover(1), rollover(0)
    if now.weekday() == 0:  # monday before rollover: last session was thursday -> friday
        return rollover(4), rollover(3)
    return rollover(2), rollover(1)


def calc_pivot(api, market_id, now=None):
    """
    Calculate Pivot points for Support and Resistance Levels from the previous trading day
    :param api: GCapiClient
    :param market_id: market ID
    :param now: aware datetime to measure from (defaults to the current time)
    :return: Returns dictionary of support and resistance levels
    """
    start, end = previous_session(now)
    resp = api.get_prices(market_id, from_ts=to_unix(start), to_ts=to_unix(end))
    time.sleep(0.3)
    df = pd.DataFrame(resp["PriceTicks"])
    high = df["Price"].max()
    low = df["Price"].min()
    close = df["Price"].iloc[-1]
    SnR = {}
    SnR["PP"] = (high + low + close) / 3
    SnR["R1"] = (2 * SnR["PP"]) - low
    SnR["S1"] = (2 * SnR["PP"]) - high
    SnR["R2"] = SnR["PP"] + (high - low)
    SnR["S2"] = SnR["PP"] - (high - low)
    SnR["R3"] = high + 2 * (SnR["PP"] - low)
    SnR["S3"] = low - 2 * (high - SnR["PP"])
    return SnR
