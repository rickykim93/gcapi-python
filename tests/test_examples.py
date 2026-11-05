"""The examples must import without side effects, and use UTC-aware dates."""

import importlib.util
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

EXAMPLES_DIR = pathlib.Path(__file__).resolve().parent.parent / "examples"
EXAMPLES = sorted(EXAMPLES_DIR.glob("*.py"))

MS_2023_03_10_UTC = 1678406400000


def load_example(path):
    spec = importlib.util.spec_from_file_location(f"example_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_examples_are_found():
    assert {p.name for p in EXAMPLES} >= {"streaming_example.py", "technical_indicators.py"}


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_imports_cleanly(path, rsps):
    # rsps is active: any HTTP request at import time would raise ConnectionError
    load_example(path)
    assert len(rsps.calls) == 0


# --- technical_indicators -------------------------------------------------------


@pytest.fixture
def ti():
    return load_example(EXAMPLES_DIR / "technical_indicators.py")


class StubApi:
    """Returns one tick per get_prices call: at the latest time, or exactly at to_ts."""

    def __init__(self):
        self.calls = []

    def get_prices(self, market_id, num_ticks=None, from_ts=None, to_ts=None):
        self.calls.append({"from_ts": from_ts, "to_ts": to_ts})
        ms = MS_2023_03_10_UTC if to_ts is None else to_ts * 1000
        ticks = [{"TickDate": f"/Date({ms})/", "Price": 1.0 + len(self.calls) / 100}]
        if from_ts is not None:
            ticks = [{"TickDate": f"/Date({ms})/", "Price": p} for p in (1.10, 1.30, 1.00, 1.20)]
        return {"PriceTicks": ticks}


def test_to_unix_requires_aware_datetime(ti):
    assert ti.to_unix(datetime(2023, 3, 10, tzinfo=timezone.utc)) == MS_2023_03_10_UTC // 1000
    with pytest.raises(ValueError):
        ti.to_unix(datetime(2023, 3, 10))


def test_hourly_rsi_walks_back_one_hour_in_utc(ti):
    api = StubApi()
    ti.calc_hourly_rsi(api, 401484317, n=3)
    start = MS_2023_03_10_UTC // 1000
    assert [c["to_ts"] for c in api.calls] == [None, start - 3600, start - 7200, start - 10800]


def test_5m_ema_walks_back_five_minutes(ti):
    api = StubApi()
    ti.calc_5m_ema(api, 401484317)
    assert len(api.calls) == 43
    assert api.calls[2]["to_ts"] == MS_2023_03_10_UTC // 1000 - 600


@pytest.mark.parametrize(
    "now_utc, expected_start_utc, expected_end_utc",
    [
        # Wed 2023-03-08 23:00 UTC = 18:00 EST (after rollover): Tue 17:00 -> Wed 17:00 New York
        (datetime(2023, 3, 8, 23), datetime(2023, 3, 7, 22), datetime(2023, 3, 8, 22)),
        # Wed 2023-03-08 15:00 UTC = 10:00 EST (before rollover): Mon 17:00 -> Tue 17:00
        (datetime(2023, 3, 8, 15), datetime(2023, 3, 6, 22), datetime(2023, 3, 7, 22)),
        # Mon 2023-03-06 15:00 UTC (before rollover): Thu 17:00 -> Fri 17:00
        (datetime(2023, 3, 6, 15), datetime(2023, 3, 2, 22), datetime(2023, 3, 3, 22)),
        # Sun 2023-03-05 23:00 UTC = 18:00 EST: Thu 17:00 -> Fri 17:00
        (datetime(2023, 3, 5, 23), datetime(2023, 3, 2, 22), datetime(2023, 3, 3, 22)),
        # After US DST starts (EDT, UTC-4): Wed 2023-03-15 22:00 UTC = 18:00 EDT
        (datetime(2023, 3, 15, 22), datetime(2023, 3, 14, 21), datetime(2023, 3, 15, 21)),
    ],
)
def test_previous_session_uses_new_york_rollover(ti, now_utc, expected_start_utc, expected_end_utc):
    start, end = ti.previous_session(now_utc.replace(tzinfo=timezone.utc))
    assert start == expected_start_utc.replace(tzinfo=timezone.utc)
    assert end == expected_end_utc.replace(tzinfo=timezone.utc)
    assert end - start == timedelta(days=1)


def test_calc_pivot_sends_utc_session_bounds(ti, monkeypatch):
    monkeypatch.setattr(ti.time, "sleep", lambda s: None)
    api = StubApi()
    snr = ti.calc_pivot(api, 401484317, now=datetime(2023, 3, 8, 23, tzinfo=timezone.utc))

    assert api.calls == [{"from_ts": 1678226400, "to_ts": 1678312800}]  # 2023-03-07/08 22:00 UTC
    high, low, close = 1.30, 1.00, 1.20
    assert snr["PP"] == pytest.approx((high + low + close) / 3)
    assert snr["R1"] == pytest.approx(2 * snr["PP"] - low)
    assert snr["S1"] == pytest.approx(2 * snr["PP"] - high)
