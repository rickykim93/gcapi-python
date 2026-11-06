"""trade_order, list_open_positions, list_active_orders, cancel_order."""

import pytest

from tests.conftest import BASE, MARKET_ID, MARKET_NAME, TRADING_ACCOUNT_ID

NEW_TRADE_URL = f"{BASE}/order/newtradeorder"
NEW_STOP_LIMIT_URL = f"{BASE}/order/newstoplimitorder"

QTY = 1000
OFFER = 1.37871


def _base_order(direction="buy", **overrides):
    body = {
        "Direction": direction,
        "MarketId": MARKET_ID,
        "Quantity": QTY,
        "MarketName": MARKET_NAME,
        "TradingAccountId": TRADING_ACCOUNT_ID,
        "OfferPrice": OFFER,
    }
    body.update(overrides)
    return body


# --- trade_order -------------------------------------------------------------


def test_market_order_uses_stored_account_and_market(rsps, api, samples, sent):
    rsps.post(NEW_TRADE_URL, json=samples["trade_ok"])

    assert api.trade_order(QTY, OFFER, "buy") == samples["trade_ok"]
    assert sent().method == "POST"
    assert sent().url == NEW_TRADE_URL
    assert sent().json == _base_order()


def test_market_order_explicit_args_and_direction_lowercased(rsps, api, samples, sent):
    rsps.post(NEW_TRADE_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "SELL", trading_acc_id=999, market_id=111, market_name="EUR/USD")
    assert sent().json == _base_order("sell", TradingAccountId=999, MarketId=111, MarketName="EUR/USD")


def test_stop_limit_order_with_trigger_price(rsps, api, samples, sent):
    rsps.post(NEW_STOP_LIMIT_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "buy", trigger_price=1.36500)
    assert sent().url == NEW_STOP_LIMIT_URL
    assert sent().json == _base_order(TriggerPrice=1.36500)


def test_if_done_stop_loss(rsps, api, samples, sent):
    rsps.post(NEW_TRADE_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "buy", stop_loss=1.36000)
    assert sent().json == _base_order(
        IfDone=[{"Stop": {"TriggerPrice": 1.36000, "Direction": "sell", "Quantity": QTY}}]
    )


def test_if_done_take_profit(rsps, api, samples, sent):
    rsps.post(NEW_TRADE_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "buy", take_profit=1.39000)
    assert sent().json == _base_order(
        IfDone=[{"Limit": {"TriggerPrice": 1.39000, "Direction": "sell", "Quantity": QTY}}]
    )


def test_if_done_stop_loss_and_take_profit_on_sell(rsps, api, samples, sent):
    rsps.post(NEW_TRADE_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "sell", stop_loss=1.39000, take_profit=1.36000)
    assert sent().json == _base_order(
        "sell",
        IfDone=[
            {
                "Stop": {"TriggerPrice": 1.39000, "Direction": "buy", "Quantity": QTY},
                "Limit": {"TriggerPrice": 1.36000, "Direction": "buy", "Quantity": QTY},
            }
        ],
    )


def test_stop_limit_order_with_if_done(rsps, api, samples, sent):
    rsps.post(NEW_STOP_LIMIT_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "buy", trigger_price=1.36500, stop_loss=1.36000)
    assert sent().url == NEW_STOP_LIMIT_URL
    assert sent().json == _base_order(
        TriggerPrice=1.36500,
        IfDone=[{"Stop": {"TriggerPrice": 1.36000, "Direction": "sell", "Quantity": QTY}}],
    )


def test_bid_price_is_sent_when_given(rsps, api, samples, sent):
    rsps.post(NEW_TRADE_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "sell", bid_price=1.37861)
    assert sent().json == _base_order("sell", BidPrice=1.37861)


def test_price_tolerance_is_sent_when_given_including_zero(rsps, api, samples, sent):
    rsps.post(NEW_TRADE_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "buy", price_tolerance=0)
    assert sent().json == _base_order(PriceTolerance=0)

    api.trade_order(QTY, OFFER, "buy", price_tolerance=2.5)
    assert sent().json == _base_order(PriceTolerance=2.5)


def test_stop_order_with_bid_price_and_tolerance(rsps, api, samples, sent):
    rsps.post(NEW_STOP_LIMIT_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "sell", trigger_price=1.36500, bid_price=1.37861, price_tolerance=1)
    assert sent().url == NEW_STOP_LIMIT_URL
    assert sent().json == _base_order("sell", TriggerPrice=1.36500, BidPrice=1.37861, PriceTolerance=1)


def test_positional_argument_order_unchanged(rsps, api, samples, sent):
    """quantity, offer_price, direction, trading_acc_id, market_id, market_name,
    stop_loss, take_profit, trigger_price -- as in 0.0.9."""
    rsps.post(NEW_STOP_LIMIT_URL, json=samples["trade_ok"])

    api.trade_order(QTY, OFFER, "buy", 999, 111, "EUR/USD", 1.36, 1.39, 1.365)
    assert sent().json == _base_order(
        TradingAccountId=999,
        MarketId=111,
        MarketName="EUR/USD",
        TriggerPrice=1.365,
        IfDone=[
            {
                "Stop": {"TriggerPrice": 1.36, "Direction": "sell", "Quantity": QTY},
                "Limit": {"TriggerPrice": 1.39, "Direction": "sell", "Quantity": QTY},
            }
        ],
    )


@pytest.mark.parametrize("direction", ["long", "", "b"])
def test_invalid_direction_raises_and_sends_nothing(rsps, api, direction):
    with pytest.raises(ValueError):
        api.trade_order(QTY, OFFER, direction)
    assert len(rsps.calls) == 0


# --- update_trade ------------------------------------------------------------

UPDATE_URL = f"{BASE}/order/updatetradeorder"
TRADE_ID = 654321987


def _base_update(direction="buy", **overrides):
    body = {
        "OrderId": TRADE_ID,
        "Direction": direction,
        "MarketId": MARKET_ID,
        "Quantity": QTY,
        "MarketName": MARKET_NAME,
        "TradingAccountId": TRADING_ACCOUNT_ID,
    }
    body.update(overrides)
    return body


def test_update_trade_minimal(rsps, api, samples, sent):
    rsps.post(UPDATE_URL, json=samples["trade_ok"])

    assert api.update_trade(TRADE_ID, QTY, "buy") == samples["trade_ok"]
    assert sent().method == "POST"
    assert sent().url == UPDATE_URL
    assert sent().json == _base_update()


def test_update_trade_sets_stop_loss_and_take_profit(rsps, api, samples, sent):
    rsps.post(UPDATE_URL, json=samples["trade_ok"])

    api.update_trade(TRADE_ID, QTY, "buy", stop_loss=1.36000, take_profit=1.39000)
    assert sent().json == _base_update(
        IfDone=[
            {
                "Stop": {"TriggerPrice": 1.36000, "Direction": "sell", "Quantity": QTY},
                "Limit": {"TriggerPrice": 1.39000, "Direction": "sell", "Quantity": QTY},
            }
        ]
    )


def test_update_trade_sell_with_prices_and_tolerance(rsps, api, samples, sent):
    rsps.post(UPDATE_URL, json=samples["trade_ok"])

    api.update_trade(
        TRADE_ID, QTY, "SELL", offer_price=1.37871, bid_price=1.37861, price_tolerance=0, stop_loss=1.39000
    )
    assert sent().json == _base_update(
        "sell",
        OfferPrice=1.37871,
        BidPrice=1.37861,
        PriceTolerance=0,
        IfDone=[{"Stop": {"TriggerPrice": 1.39000, "Direction": "buy", "Quantity": QTY}}],
    )


def test_update_trade_explicit_account_and_market(rsps, api, samples, sent):
    rsps.post(UPDATE_URL, json=samples["trade_ok"])

    api.update_trade(TRADE_ID, QTY, "buy", trading_acc_id=999, market_id=111, market_name="EUR/USD")
    assert sent().json == _base_update(TradingAccountId=999, MarketId=111, MarketName="EUR/USD")


def test_update_trade_invalid_direction_raises_and_sends_nothing(rsps, api):
    with pytest.raises(ValueError):
        api.update_trade(TRADE_ID, QTY, "long")
    assert len(rsps.calls) == 0


# --- list_open_positions -----------------------------------------------------


def test_list_open_positions_default_account(rsps, api, samples, sent):
    rsps.get(f"{BASE}/order/openpositions", json=samples["open_positions"])

    assert api.list_open_positions() == samples["open_positions"]
    assert sent().method == "GET"
    assert sent().url == f"{BASE}/order/openpositions?TradingAccountId={TRADING_ACCOUNT_ID}"


def test_list_open_positions_explicit_account(rsps, api, samples, sent):
    rsps.get(f"{BASE}/order/openpositions", json=samples["open_positions"])

    api.list_open_positions(trading_acc_id=999)
    assert sent().url == f"{BASE}/order/openpositions?TradingAccountId=999"


# --- list_active_orders ------------------------------------------------------


def test_list_active_orders_default_account(rsps, api, samples, sent):
    rsps.post(f"{BASE}/order/activeorders", json=samples["active_orders"])

    assert api.list_active_orders() == samples["active_orders"]
    assert sent().method == "POST"
    assert sent().url == f"{BASE}/order/activeorders"
    assert sent().json == {"TradingAccountId": TRADING_ACCOUNT_ID, "MaxResults": 100}


def test_list_active_orders_explicit_account(rsps, api, samples, sent):
    rsps.post(f"{BASE}/order/activeorders", json=samples["active_orders"])

    api.list_active_orders(trading_acc_id=999)
    assert sent().json == {"TradingAccountId": 999, "MaxResults": 100}


# --- cancel_order ------------------------------------------------------------

ORDER_ID = 654322001


def test_cancel_order_default_account(rsps, api, samples, sent):
    rsps.post(f"{BASE}/order/cancel", json=samples["cancel_ok"])

    assert api.cancel_order(ORDER_ID) == samples["cancel_ok"]
    assert sent().method == "POST"
    assert sent().url == f"{BASE}/order/cancel"
    assert sent().json == {"TradingAccountId": TRADING_ACCOUNT_ID, "OrderId": ORDER_ID, "MarketId": MARKET_ID}


def test_cancel_order_explicit_account(rsps, api, samples, sent):
    rsps.post(f"{BASE}/order/cancel", json=samples["cancel_ok"])

    api.cancel_order(ORDER_ID, trading_acc_id=999)
    assert sent().json == {"TradingAccountId": 999, "OrderId": ORDER_ID, "MarketId": MARKET_ID}


def test_cancel_order_explicit_market(rsps, api, samples, sent):
    rsps.post(f"{BASE}/order/cancel", json=samples["cancel_ok"])

    api.cancel_order(ORDER_ID, market_id=111)
    assert sent().json == {"TradingAccountId": TRADING_ACCOUNT_ID, "OrderId": ORDER_ID, "MarketId": 111}


def test_cancel_order_without_loaded_market_omits_market_id(rsps, client, samples, sent):
    rsps.post(f"{BASE}/order/cancel", json=samples["cancel_ok"])

    client.cancel_order(ORDER_ID, trading_acc_id=999)
    assert sent().json == {"TradingAccountId": 999, "OrderId": ORDER_ID}


def test_explicit_account_works_without_get_account_info(rsps, client, samples, sent):
    """Passing trading_acc_id must not require self.trading_account_id to exist."""
    rsps.post(f"{BASE}/order/activeorders", json=samples["active_orders"])
    rsps.post(f"{BASE}/order/cancel", json=samples["cancel_ok"])

    client.list_active_orders(trading_acc_id=999)
    assert sent().json["TradingAccountId"] == 999
    client.cancel_order(ORDER_ID, trading_acc_id=999)
    assert sent().json["TradingAccountId"] == 999
