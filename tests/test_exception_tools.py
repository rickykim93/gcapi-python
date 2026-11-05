"""GCapiException getters and gcapi_tools helpers."""
from datetime import datetime, timezone

import pytest

from gcapi.gcapi_exception import GCapiException
from gcapi.gcapi_tools import INTERVAL, check_interval, check_span, format_date

# =============================================================================
# GCapiException
# =============================================================================


def test_exception_getters_return_fields(samples):
    exc = GCapiException(samples["error_full"])
    assert exc.get_exception() == samples["error_full"]
    assert exc.get_status_code() == 3
    assert exc.get_http_status() == 400
    assert exc.get_error_message() == "Market is closed"
    assert exc.get_error_code() == 4000
    assert exc.get_additional_info() == "MarketId 401484317"


def test_exception_is_raisable_exception(samples):
    with pytest.raises(Exception):
        raise GCapiException(samples["error_full"])


def test_exception_getters_return_none_for_empty_fields(samples):
    payload = dict(samples["error_full"], ErrorMessage=None, AdditionalInfo="")
    exc = GCapiException(payload)
    assert exc.get_error_message() is None
    assert exc.get_additional_info() is None


@pytest.mark.xfail(
    strict=True,
    raises=KeyError,
    reason="new bug: getters index the dict directly, so a missing key (e.g. StatusCode on a 401 error DTO) raises KeyError",
)
def test_exception_getters_tolerate_missing_keys(samples):
    exc = GCapiException(samples["login_error_dto"])
    assert exc.get_error_code() == 4010
    assert exc.get_status_code() is None
    assert exc.get_additional_info() is None


# =============================================================================
# format_date
# =============================================================================

MS_2023_03_10_UTC = 1678406400000


def test_format_date_returns_datetime():
    assert isinstance(format_date(f"/Date({MS_2023_03_10_UTC})/"), datetime)


@pytest.mark.parametrize(
    "raw",
    [f"/Date({MS_2023_03_10_UTC}-0500)/", f"/Date({MS_2023_03_10_UTC}+0000)/", MS_2023_03_10_UTC],
)
def test_format_date_uses_first_number_only(raw):
    assert format_date(raw) == format_date(f"/Date({MS_2023_03_10_UTC})/")


def test_format_date_is_utc():
    assert format_date(f"/Date({MS_2023_03_10_UTC})/") == datetime(2023, 3, 10, tzinfo=timezone.utc)
    assert format_date(f"/Date({MS_2023_03_10_UTC})/").tzinfo is not None


# =============================================================================
# check_interval
# =============================================================================


@pytest.mark.parametrize("interval", INTERVAL)
def test_check_interval_accepts_valid(interval):
    assert check_interval(interval) == interval


@pytest.mark.parametrize("interval", ["FORTNIGHT", "", None, "SECOND"])
def test_check_interval_falls_back_to_hour(interval):
    assert check_interval(interval) == "HOUR"


# =============================================================================
# check_span
# =============================================================================


@pytest.mark.parametrize("interval", ["DAY", "WEEK", "MONTH"])
def test_check_span_is_1_for_day_and_longer(interval):
    assert check_span(interval, 5) == 1


@pytest.mark.parametrize("interval, span", [("HOUR", 3), ("HOUR", 12), ("MINUTE", 4), ("MINUTE", 60)])
def test_check_span_invalid_falls_back_to_1(interval, span):
    assert check_span(interval, span) == 1


@pytest.mark.parametrize("interval, span", [("HOUR", 1), ("MINUTE", 1)])
def test_check_span_1_is_valid(interval, span):
    assert check_span(interval, span) == 1


@pytest.mark.parametrize(
    "interval, span",
    [("HOUR", 2), ("HOUR", 4), ("HOUR", 8),
     ("MINUTE", 2), ("MINUTE", 3), ("MINUTE", 5), ("MINUTE", 10), ("MINUTE", 15), ("MINUTE", 30)],
)
def test_check_span_keeps_valid_span(interval, span):
    assert check_span(interval, span) == span


@pytest.mark.parametrize("interval, span", [("HOUR", "4"), ("MINUTE", "15")])
def test_check_span_accepts_numeric_strings(interval, span):
    assert check_span(interval, span) == int(span)


@pytest.mark.parametrize("span", [None, "abc", 2.5])
def test_check_span_non_numeric_falls_back_to_1(span):
    assert check_span("HOUR", span) == 1
