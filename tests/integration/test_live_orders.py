"""Order tests against the live API. Opt-in with GCAPI_ALLOW_ORDERS=1, and use a demo account.

Only pending stop/limit orders are placed, priced ~10% away from the market so they cannot fill,
and the placed_orders fixture cancels every one of them afterwards. No market orders, so
update_trade (which needs an open trade) is not covered here.
"""

import os

import pytest

from tests.integration._helpers import active_orders

pytestmark = pytest.mark.integration

QUANTITY = float(os.environ.get("GCAPI_ORDER_QUANTITY", "1000"))


def _far_buy_limit(api):
    """A buy limit ~10% below the market. Rounded to 2 decimals, a multiple of any FX tick size."""
    bid = api.get_prices(price_type="BID")
    offer = api.get_prices(price_type="ASK")
    return bid, offer, round(offer * 0.9, 2)


def _place(api, placed_orders, **kwargs):
    resp = api.trade_order(**kwargs)
    order_id = resp.get("OrderId")
    if order_id:
        placed_orders.append(order_id)
    assert order_id, f"order rejected: {resp}"
    return order_id


def test_stop_limit_order_is_listed_and_cancelled(live_api, placed_orders):
    bid, offer, trigger = _far_buy_limit(live_api)
    order_id = _place(
        live_api,
        placed_orders,
        quantity=QUANTITY,
        offer_price=offer,
        direction="buy",
        trigger_price=trigger,
        bid_price=bid,
        price_tolerance=0,
    )
    assert order_id in {o["OrderId"] for o in active_orders(live_api)}

    resp = live_api.cancel_order(order_id)  # sends MarketId
    assert resp.get("OrderId") == order_id, f"cancel failed: {resp}"
    assert order_id not in {o["OrderId"] for o in active_orders(live_api)}


def test_stop_limit_order_with_if_done(live_api, placed_orders):
    bid, offer, trigger = _far_buy_limit(live_api)
    _place(
        live_api,
        placed_orders,
        quantity=QUANTITY,
        offer_price=offer,
        direction="buy",
        trigger_price=trigger,
        bid_price=bid,
        stop_loss=round(trigger * 0.98, 2),
        take_profit=round(trigger * 1.02, 2),
    )
