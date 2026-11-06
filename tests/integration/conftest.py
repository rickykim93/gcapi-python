"""Fixtures for the opt-in live integration tests.

These tests talk to the real Gain Capital API, so they are skipped unless credentials are set:

    GCAPI_USERNAME, GCAPI_PASSWORD, GCAPI_APPKEY   required for every integration test
    GCAPI_MARKET                                   market to use (default "EUR/USD")
    GCAPI_ALLOW_ORDERS=1                           also run the order tests (pending stop/limit orders,
                                                   placed far from the market and always cancelled)
    GCAPI_ORDER_QUANTITY                           order size for the order tests (default 1000)

Use a demo account. CI never runs these (it deselects them with -m "not integration").
"""

import os

import pytest

from gcapi import GCapiClient
from tests.integration._helpers import active_orders

CREDENTIAL_VARS = ("GCAPI_USERNAME", "GCAPI_PASSWORD", "GCAPI_APPKEY")


@pytest.fixture(scope="session")
def live_api():
    missing = [v for v in CREDENTIAL_VARS if not os.environ.get(v)]
    if missing:
        pytest.skip(f"integration tests need {', '.join(missing)}")
    api = GCapiClient(
        username=os.environ["GCAPI_USERNAME"],
        password=os.environ["GCAPI_PASSWORD"],
        appkey=os.environ["GCAPI_APPKEY"],
    )
    api.get_account_info()
    api.get_market_info(os.environ.get("GCAPI_MARKET", "EUR/USD"))
    return api


@pytest.fixture
def orders_allowed():
    if os.environ.get("GCAPI_ALLOW_ORDERS") != "1":
        pytest.skip("order tests need GCAPI_ALLOW_ORDERS=1")


@pytest.fixture
def placed_orders(orders_allowed, live_api):  # check the opt-in before logging in
    """Collects the IDs of orders a test places and cancels every one of them afterwards,
    whether the test passed or failed."""
    order_ids = []
    yield order_ids
    errors = []
    for order_id in order_ids:
        try:
            live_api.cancel_order(order_id)
        except Exception as err:  # keep cancelling the rest
            errors.append(f"{order_id}: {err!r}")
    still_active = {o["OrderId"] for o in active_orders(live_api)} & set(order_ids)
    if errors or still_active:
        pytest.fail(
            f"could not cancel test orders, cancel them manually: errors={errors} still_active={sorted(still_active)}"
        )
