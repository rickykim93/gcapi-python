"""get_prices and get_ohlc: every endpoint branch, plus DataFrame conversion."""
from datetime import datetime, timezone

import pandas as pd
import pytest

from gcapi.gcapi_exception import GCapiException
from gcapi.gcapi_tools import format_date
from tests.conftest import BASE, MARKET_ID

FROM_TS = 1678406400  # 2023-03-10 00:00:00 UTC
TO_TS = 1678410000    # 2023-03-10 01:00:00 UTC

MARKET = f"{BASE}/market/{MARKET_ID}"
PATH = f"/TradingAPI/market/{MARKET_ID}"


# =============================================================================
# get_prices
# =============================================================================

def test_get_prices_latest_tick_returns_single_price(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/tickhistory", json=samples["ticks"])

    assert api.get_prices() == 1.37865
    assert sent().method == "GET"
    assert sent().url == f"{MARKET}/tickhistory?PriceTicks=1&priceType=MID"


def test_get_prices_num_ticks_returns_full_response(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/tickhistory", json=samples["ticks"])

    assert api.get_prices(num_ticks=3) == samples["ticks"]
    assert sent().url == f"{MARKET}/tickhistory?PriceTicks=3&priceType=MID"


def test_get_prices_explicit_market_id_and_price_type(rsps, api, samples, sent):
    rsps.get(f"{BASE}/market/999/tickhistory", json=samples["ticks"])

    api.get_prices(market_id=999, num_ticks=3, price_type="bid")
    assert sent().url == f"{BASE}/market/999/tickhistory?PriceTicks=3&priceType=BID"


def test_get_prices_between(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/tickhistorybetween", json=samples["ticks"])

    assert api.get_prices(from_ts=FROM_TS, to_ts=TO_TS) == samples["ticks"]
    assert sent().url == (
        f"{MARKET}/tickhistorybetween?fromTimeStampUTC={FROM_TS}&toTimestampUTC={TO_TS}&priceType=MID"
    )


def _register_tick_before_after(rsps, samples):
    for endpoint in ("tickhistorybefore", "tickhistoryafter"):
        rsps.get(f"{MARKET}/{endpoint}", json=samples["ticks"])


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="swapped before/after branches: from_ts-only calls tickhistorybefore with toTimeStampUTC=None",
)
def test_get_prices_from_ts_only_requests_ticks_after(rsps, api, samples, sent):
    _register_tick_before_after(rsps, samples)

    api.get_prices(num_ticks=3, from_ts=FROM_TS)
    assert sent().path == f"{PATH}/tickhistoryafter"
    assert sent().params == {"maxResults": "3", "fromTimeStampUTC": str(FROM_TS), "priceType": "MID"}


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="swapped before/after branches: to_ts-only calls tickhistoryafter with fromTimeStampUTC=None",
)
def test_get_prices_to_ts_only_requests_ticks_before(rsps, api, samples, sent):
    _register_tick_before_after(rsps, samples)

    api.get_prices(num_ticks=3, to_ts=TO_TS)
    assert sent().path == f"{PATH}/tickhistorybefore"
    assert sent().params == {"maxResults": "3", "toTimeStampUTC": str(TO_TS), "priceType": "MID"}


def test_get_prices_error_raises(rsps, api, samples):
    rsps.get(f"{MARKET}/tickhistory", json=samples["error_full"], status=400)
    with pytest.raises(GCapiException):
        api.get_prices()


# =============================================================================
# get_ohlc
# =============================================================================

OHLC_COLUMNS = ["BarDate", "Open", "High", "Low", "Close"]


def test_get_ohlc_latest_bar_returns_raw_dict(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    assert api.get_ohlc() == samples["bars"]["PriceBars"][0]
    assert sent().method == "GET"
    assert sent().url == f"{MARKET}/barhistory?interval=HOUR&span=1&PriceBars=1"


def test_get_ohlc_num_ticks_returns_dataframe(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    df = api.get_ohlc(num_ticks=4, interval="DAY")
    assert sent().url == f"{MARKET}/barhistory?interval=DAY&span=1&PriceBars=4"
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == OHLC_COLUMNS
    assert df["Close"].tolist() == [43.535, 42.445, 42.885, 41.315]


def test_get_ohlc_dataframe_converts_bar_dates(rsps, api, samples):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    df = api.get_ohlc(num_ticks=4, interval="DAY")
    assert pd.api.types.is_datetime64_any_dtype(df["BarDate"])
    expected = [format_date(b["BarDate"]) for b in samples["bars"]["PriceBars"]]
    assert [ts.to_pydatetime() for ts in df["BarDate"]] == expected


def test_get_ohlc_invalid_interval_and_span_fall_back_to_defaults(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    api.get_ohlc(num_ticks=4, interval="FORTNIGHT", span=7)
    assert sent().params["interval"] == "HOUR"
    assert sent().params["span"] == "1"


def test_get_ohlc_span_forced_to_1_for_day(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    api.get_ohlc(num_ticks=4, interval="DAY", span=5)
    assert sent().params["span"] == "1"


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="check_span compares span against the whole SPAN_M/SPAN_H list, so a valid span is always reset to 1",
)
def test_get_ohlc_valid_span_is_sent(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    api.get_ohlc(num_ticks=4, interval="MINUTE", span=15)
    assert sent().params["span"] == "15"


def test_get_ohlc_between(rsps, api, samples, sent):
    rsps.get(f"{MARKET}/barhistorybetween", json=samples["bars"])

    df = api.get_ohlc(interval="HOUR", from_ts=FROM_TS, to_ts=TO_TS)
    assert sent().url == (
        f"{MARKET}/barhistorybetween?interval=HOUR&span=1"
        f"&fromTimeStampUTC={FROM_TS}&toTimestampUTC={TO_TS}"
    )
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == OHLC_COLUMNS


def _register_bar_before_after(rsps, samples):
    # include tickhistoryafter so the current (buggy) code gets a response
    # and the test fails on its assertion, not on a ConnectionError
    for endpoint in ("barhistorybefore", "barhistoryafter", "tickhistoryafter"):
        rsps.get(f"{MARKET}/{endpoint}", json=samples["bars"])


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="swapped before/after branches: from_ts-only sends toTimeStampUTC=None instead of fromTimeStampUTC",
)
def test_get_ohlc_from_ts_only_sends_from_timestamp(rsps, api, samples, sent):
    _register_bar_before_after(rsps, samples)

    api.get_ohlc(num_ticks=4, from_ts=FROM_TS)
    assert sent().params == {
        "interval": "HOUR", "span": "1", "maxResults": "4", "fromTimeStampUTC": str(FROM_TS),
    }


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="get_ohlc's 'after' branch uses tickhistoryafter instead of barhistoryafter (and is also swapped)",
)
def test_get_ohlc_from_ts_only_uses_barhistoryafter(rsps, api, samples, sent):
    _register_bar_before_after(rsps, samples)

    api.get_ohlc(num_ticks=4, from_ts=FROM_TS)
    assert sent().path == f"{PATH}/barhistoryafter"


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="swapped before/after branches: to_ts-only calls tickhistoryafter with fromTimeStampUTC=None",
)
def test_get_ohlc_to_ts_only_requests_bars_before(rsps, api, samples, sent):
    _register_bar_before_after(rsps, samples)

    api.get_ohlc(num_ticks=4, to_ts=TO_TS)
    assert sent().path == f"{PATH}/barhistorybefore"
    assert sent().params == {
        "interval": "HOUR", "span": "1", "maxResults": "4", "toTimeStampUTC": str(TO_TS),
    }


def test_get_ohlc_excludes_partial_bar_by_default(rsps, api, samples):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    df = api.get_ohlc(num_ticks=4, interval="DAY")
    assert len(df) == 4
    assert df["Close"].iloc[-1] == 41.315


@pytest.mark.xfail(
    strict=True,
    raises=TypeError,
    reason="issue #10: PartialPriceBar is always dropped; get_ohlc has no include_partial option",
)
def test_get_ohlc_include_partial_appends_forming_bar(rsps, api, samples):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    df = api.get_ohlc(num_ticks=4, interval="DAY", include_partial=True)
    assert len(df) == 5
    assert df["Close"].tolist() == [43.535, 42.445, 42.885, 41.315, 40.185]
    assert df["BarDate"].iloc[-1] == df["BarDate"].max()


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="issue #10: local-time conversion; BarDate should be tz-aware UTC",
)
def test_get_ohlc_bar_dates_are_utc(rsps, api, samples):
    rsps.get(f"{MARKET}/barhistory", json=samples["bars"])

    df = api.get_ohlc(num_ticks=4, interval="DAY")
    assert str(df["BarDate"].dt.tz) == "UTC"
    assert df["BarDate"].iloc[0] == pd.Timestamp(datetime(2023, 3, 6, tzinfo=timezone.utc))


def test_get_ohlc_error_raises(rsps, api, samples):
    rsps.get(f"{MARKET}/barhistory", json=samples["error_full"], status=400)
    with pytest.raises(GCapiException):
        api.get_ohlc(num_ticks=4)
