"""Helpers shared by the live integration tests."""


def active_orders(api):
    """Flatten /order/activeorders into the order dicts (stop/limit orders are nested)."""
    resp = api.list_active_orders()
    orders = []
    for entry in resp.get("ActiveOrders") or []:
        order = entry.get("StopLimitOrder") or entry.get("TradeOrder") or entry
        orders.append(order)
    return orders
