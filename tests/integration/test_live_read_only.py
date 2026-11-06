"""Read-only calls against the live API. Nothing here places or changes orders."""

import time
from datetime import datetime, timezone

import pandas as pd
import pytest

from gcapi.gcapi_exception import GCapiException

pytestmark = pytest.mark.integration


def test_account_and_margin(live_api):
    assert live_api.trading_account_id
    assert live_api.get_account_info(get="TradingAccountId") == live_api.trading_account_id
    margin = live_api.get_margin_info()
    assert "Cash" in margin


def test_market_info(live_api):
    assert isinstance(live_api.market_id, int)


def test_unknown_market_raises(live_api):
    name, market_id = live_api.market_name, live_api.market_id
    try:
        with pytest.raises(GCapiException):
            live_api.get_market_info("NOT/AMARKET")
    finally:
        # get_market_info stores the name before validating it; put the real market back
        live_api.market_name, live_api.market_id = name, market_id


def test_latest_price(live_api):
    for price_type in ("MID", "BID", "ASK"):
        assert live_api.get_prices(price_type=price_type) > 0


def test_price_history_directions(live_api):
    now = int(time.time())
    week_ago = now - 7 * 24 * 3600
    after = live_api.get_prices(num_ticks=5, from_ts=week_ago)["PriceTicks"]
    before = live_api.get_prices(num_ticks=5, to_ts=now)["PriceTicks"]
    assert after and before


def test_ohlc_dataframe_is_utc(live_api):
    df = live_api.get_ohlc(num_ticks=10, interval="HOUR")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert str(df["BarDate"].dt.tz) == "UTC"
    assert df["BarDate"].max() <= pd.Timestamp(datetime.now(timezone.utc))


def test_ohlc_include_partial_adds_at_most_one_bar(live_api):
    completed = live_api.get_ohlc(num_ticks=10, interval="DAY")
    with_partial = live_api.get_ohlc(num_ticks=10, interval="DAY", include_partial=True)
    assert len(with_partial) - len(completed) in (0, 1)  # 0 when no bar is forming (e.g. weekends)


def test_ohlc_span(live_api):
    df = live_api.get_ohlc(num_ticks=4, interval="MINUTE", span=15)
    gaps = df["BarDate"].diff().dropna()
    assert (gaps >= pd.Timedelta(minutes=15)).all()


def test_positions_and_orders_listing(live_api):
    assert isinstance(live_api.list_open_positions(), dict)
    assert isinstance(live_api.list_active_orders(), dict)
