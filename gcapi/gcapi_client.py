import json
from typing import Any

import pandas as pd
import requests

from gcapi.gcapi_exception import GCapiException
from gcapi.gcapi_streaming import GCapiStreamingClient
from gcapi.gcapi_tools import check_interval, check_span, format_date

# A decoded JSON object returned by the API
JSONDict = dict[str, Any]


class GCapiClient:
    def __init__(self, username: str, password: str, appkey: str, proxies: dict[str, str] | None = None) -> None:
        self.rest_url = "https://ciapi.cityindex.com/TradingAPI"
        headers = {"Content-Type": "application/json"}
        data = {"UserName": username, "Password": password, "AppKey": appkey}
        r = requests.post(self.rest_url + "/session", headers=headers, proxies=proxies, json=data)
        resp = json.loads(r.text)
        if resp.get("StatusCode") != 1:
            raise GCapiException(resp)
        session = resp["Session"]
        headers = {"Content-Type": "application/json", "UserName": username, "Session": session}
        s = requests.Session()
        s.headers = headers
        if proxies is not None:
            s.proxies.update(proxies)
        self.session = s
        self.session_id = session
        self.username = username

    def get_account_info(self, get: str | None = None) -> Any:
        """
        Gets trading account general information
        :param get: retrieve specific information (e.g. TradingAccountId)
        :return: trading account information
        """
        r = self.session.get(self.rest_url + "/UserAccount/ClientAndTradingAccount")
        resp = json.loads(r.text)
        try:
            self.trading_account_id = resp["TradingAccounts"][0]["TradingAccountId"]
            if get is not None:
                return resp["TradingAccounts"][0][get]
            else:
                return resp
        except Exception as err:
            raise GCapiException(resp) from err

    def get_margin_info(self, get: str | None = None) -> Any:
        """
        Gets trading account margin information
        :param get: retrieve specific information (e.g. Cash)
        :return: trading account margin information
        """
        r = self.session.get(self.rest_url + "/margin/ClientAccountMargin")
        resp = json.loads(r.text)
        try:
            self.cash = resp["Cash"]
            if get is not None:
                return resp[get]
            else:
                return resp
        except Exception as err:
            raise GCapiException(resp) from err

    def init_streaming_client(self) -> GCapiStreamingClient:
        """
        Initalizes the Streaming Client
        :return: Streaming Client Object
        """
        self.stream_client = GCapiStreamingClient(username=self.username, session_id=self.session_id)

        return self.stream_client

    def get_market_info(self, market_name: str, get: str | None = None) -> Any:
        """
        Gets market information
        :param market_name: market name (e.g. USD/CAD)
        :param get: retrieve specific information (e.g. MarketId)
        :return: market information
        """
        r = self.session.get(self.rest_url + f"/cfd/markets?MarketName={market_name}")
        resp = json.loads(r.text)
        try:
            self.market_name = market_name
            self.market_id = resp["Markets"][0]["MarketId"]
            if get is not None:
                return resp["Markets"][0][get]
            else:
                return resp
        except Exception as err:
            raise GCapiException(resp) from err

    def get_prices(
        self,
        market_id: int | None = None,
        num_ticks: int | None = None,
        from_ts: int | None = None,
        to_ts: int | None = None,
        price_type: str | None = None,
    ) -> float | JSONDict:
        """
        Get prices
        :param market_id: market ID
        :param num_ticks: number of price ticks/data to retrieve
        :param from_ts: from timestamp UTC
        :param to_ts: to timestamp UTC
        :return: price data
        """
        if price_type is None:
            # Default to mid price
            price_type = "MID"
        else:
            price_type = price_type.upper()
        if market_id is None:
            market_id = self.market_id
        if from_ts is not None and to_ts is not None:
            r = self.session.get(
                self.rest_url
                + f"/market/{market_id}/tickhistorybetween?fromTimeStampUTC={from_ts}&toTimestampUTC={to_ts}&priceType={price_type}"
            )
        else:
            if not num_ticks:
                num_ticks = 1
            if from_ts is not None:
                # ticks after from_ts
                r = self.session.get(
                    self.rest_url
                    + f"/market/{market_id}/tickhistoryafter?maxResults={num_ticks}&fromTimeStampUTC={from_ts}&priceType={price_type}"
                )
            elif to_ts is not None:
                # ticks before to_ts
                r = self.session.get(
                    self.rest_url
                    + f"/market/{market_id}/tickhistorybefore?maxResults={num_ticks}&toTimeStampUTC={to_ts}&priceType={price_type}"
                )
            else:
                r = self.session.get(
                    self.rest_url + f"/market/{market_id}/tickhistory?PriceTicks={num_ticks}&priceType={price_type}"
                )
        resp = json.loads(r.text)
        try:
            if num_ticks == 1:
                return resp["PriceTicks"][0]["Price"]
            else:
                return resp
        except Exception as err:
            raise GCapiException(resp) from err

    def get_ohlc(
        self,
        market_id: int | None = None,
        num_ticks: int | None = None,
        interval: str = "HOUR",
        span: int | str = 1,
        from_ts: int | None = None,
        to_ts: int | None = None,
        include_partial: bool = False,
    ) -> pd.DataFrame | JSONDict:
        """
        Get the open, high, low, close of a specific market_id
        :param market_id: market ID
        :param num_ticks: number of price ticks/data to retrieve
        :param interval: MINUTE, HOUR or DAY tick interval
        :param span: it can be a combination of span with interval, 1Hour, 15 MINUTE
        :param from_ts: from timestamp UTC
        :param to_ts: to timestamp UTC
        :param include_partial: if True, append the still-forming bar (the API's PartialPriceBar) as the
                last row of the DataFrame. Only completed bars are returned by default. Has no effect when
                num_ticks is 1 (the single latest completed bar is returned as a dict).
        :return: ohlc dataframe with a timezone-aware UTC BarDate column
        """

        if market_id is None:
            market_id = self.market_id
        interval = check_interval(interval)
        span = check_span(interval, span)
        if from_ts is not None and to_ts is not None:
            r = self.session.get(
                self.rest_url
                + f"/market/{market_id}/barhistorybetween?interval={interval}&span={span}&fromTimeStampUTC={from_ts}&toTimestampUTC={to_ts}"
            )
        else:
            if not num_ticks:
                num_ticks = 1
            if from_ts is not None:
                # bars after from_ts
                r = self.session.get(
                    self.rest_url
                    + f"/market/{market_id}/barhistoryafter?interval={interval}&span={span}&maxResults={num_ticks}&fromTimeStampUTC={from_ts}"
                )
            elif to_ts is not None:
                # bars before to_ts
                r = self.session.get(
                    self.rest_url
                    + f"/market/{market_id}/barhistorybefore?interval={interval}&span={span}&maxResults={num_ticks}&toTimeStampUTC={to_ts}"
                )
            else:
                r = self.session.get(
                    self.rest_url
                    + f"/market/{market_id}/barhistory?interval={interval}&span={span}&PriceBars={num_ticks}"
                )
        resp = json.loads(r.text)

        try:
            if num_ticks == 1:
                return resp.get("PriceBars")[0]
            else:
                bars = list(resp.get("PriceBars"))
                partial = resp.get("PartialPriceBar")
                if include_partial and partial:
                    bars.append(partial)
                df_ohlc = pd.DataFrame(bars)
                df_ohlc["BarDate"] = df_ohlc["BarDate"].map(format_date)
                return df_ohlc
        except Exception as err:
            raise GCapiException(resp) from err

    @staticmethod
    def _directions(direction: str) -> tuple[str, str]:
        """
        Normalises direction and returns (direction, opposite_direction)
        :param direction: buy or sell (case-insensitive)
        """
        direction = direction.lower()
        if direction == "buy":
            return "buy", "sell"
        if direction == "sell":
            return "sell", "buy"
        raise ValueError("Please provide buy or sell for direction")

    @staticmethod
    def _if_done(
        quantity: float, opp_direction: str, stop_loss: float | None = None, take_profit: float | None = None
    ) -> list[JSONDict] | None:
        """
        Builds the IfDone list for stop loss / take profit legs, or None if neither is set
        """
        ifdone = {}
        if stop_loss:
            ifdone["Stop"] = {"TriggerPrice": stop_loss, "Direction": opp_direction, "Quantity": quantity}
        if take_profit:
            ifdone["Limit"] = {"TriggerPrice": take_profit, "Direction": opp_direction, "Quantity": quantity}
        return [ifdone] if ifdone else None

    def trade_order(
        self,
        quantity: float,
        offer_price: float | None,
        direction: str,
        trading_acc_id: int | None = None,
        market_id: int | None = None,
        market_name: str | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        trigger_price: float | None = None,
        bid_price: float | None = None,
        price_tolerance: float | None = None,
    ) -> JSONDict:
        """
        Makes a new trade order
        :param quantity: quantity to trade
        :param offer_price: offer price
        :param direction: buy or sell
        :param trading_acc_id: trading account ID
        :param market_id: market ID
        :param market_name: market name
        :param stop_loss: stop loss price
        :param take_profit: take profit price
        :param trigger_price: trigger price for stop/limit orders
        :param bid_price: bid price (needed by the API for some sell / stop orders); sent only if given
        :param price_tolerance: acceptable slippage in price points; sent only if given
        :return:
        """
        if trading_acc_id is None:
            trading_acc_id = self.trading_account_id
        if market_id is None:
            market_id = self.market_id
        if market_name is None:
            market_name = self.market_name
        api_url = "/order/newtradeorder"
        direction, opp_direction = self._directions(direction)
        trade_details = {
            "Direction": direction,
            "MarketId": market_id,
            "Quantity": quantity,
            "MarketName": market_name,
            "TradingAccountId": trading_acc_id,
            "OfferPrice": offer_price,
        }
        if bid_price is not None:
            trade_details["BidPrice"] = bid_price
        if price_tolerance is not None:
            trade_details["PriceTolerance"] = price_tolerance
        if trigger_price is not None:
            trade_details["TriggerPrice"] = trigger_price
            api_url = "/order/newstoplimitorder"
        ifdone = self._if_done(quantity, opp_direction, stop_loss, take_profit)
        if ifdone:
            trade_details["IfDone"] = ifdone
        r = self.session.post(self.rest_url + api_url, json=trade_details)
        resp = json.loads(r.text)
        return resp

    def update_trade(
        self,
        order_id: int,
        quantity: float,
        direction: str,
        offer_price: float | None = None,
        bid_price: float | None = None,
        trading_acc_id: int | None = None,
        market_id: int | None = None,
        market_name: str | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        price_tolerance: float | None = None,
    ) -> JSONDict:
        """
        Updates an existing trade order (e.g. to add or change its stop loss / take profit)

        Not yet verified against the live API by the maintainer: the request is based on PR #13's
        real-world usage. Please report what works or fails at
        https://github.com/rickykim93/gcapi-python/issues

        :param order_id: order ID of the trade to update
        :param quantity: quantity of the trade
        :param direction: buy or sell (direction of the original trade)
        :param offer_price: offer price; sent only if given
        :param bid_price: bid price; sent only if given
        :param trading_acc_id: trading account ID
        :param market_id: market ID
        :param market_name: market name
        :param stop_loss: stop loss price
        :param take_profit: take profit price
        :param price_tolerance: acceptable slippage in price points; sent only if given
        :return: API response
        """
        if trading_acc_id is None:
            trading_acc_id = self.trading_account_id
        if market_id is None:
            market_id = self.market_id
        if market_name is None:
            market_name = self.market_name
        direction, opp_direction = self._directions(direction)
        trade_details = {
            "OrderId": order_id,
            "Direction": direction,
            "MarketId": market_id,
            "Quantity": quantity,
            "MarketName": market_name,
            "TradingAccountId": trading_acc_id,
        }
        if offer_price is not None:
            trade_details["OfferPrice"] = offer_price
        if bid_price is not None:
            trade_details["BidPrice"] = bid_price
        if price_tolerance is not None:
            trade_details["PriceTolerance"] = price_tolerance
        ifdone = self._if_done(quantity, opp_direction, stop_loss, take_profit)
        if ifdone:
            trade_details["IfDone"] = ifdone
        r = self.session.post(self.rest_url + "/order/updatetradeorder", json=trade_details)
        resp = json.loads(r.text)
        return resp

    def list_open_positions(self, trading_acc_id: int | None = None) -> JSONDict:
        """
        Returns List of Open Positons in Trading Account
        """
        if trading_acc_id is None:
            trading_acc_id = self.trading_account_id

        api_url = f"/order/openpositions?TradingAccountId={trading_acc_id}"
        r = self.session.get(self.rest_url + api_url)
        resp = json.loads(r.text)

        return resp

    def list_active_orders(self, trading_acc_id: int | None = None) -> JSONDict:
        """
        Returns List of Active Order in Trading Account
        """
        if trading_acc_id is None:
            trading_acc_id = self.trading_account_id

        api_url = "/order/activeorders"
        json_data = {"TradingAccountId": trading_acc_id, "MaxResults": 100}
        r = self.session.post(self.rest_url + api_url, json=json_data)
        resp = json.loads(r.text)

        return resp

    def cancel_order(self, order_id: int, trading_acc_id: int | None = None, market_id: int | None = None) -> JSONDict:
        """
        Cancels an Active Order
        :param order_id: Order ID of the Order to Cancel
        :param trading_acc_id: trading account ID
        :param market_id: market ID of the order (required by the API since 2024); defaults to the market
                loaded by get_market_info, and is omitted if none has been loaded
        """
        if trading_acc_id is None:
            trading_acc_id = self.trading_account_id
        if market_id is None:
            market_id = getattr(self, "market_id", None)

        api_url = "/order/cancel"
        json_data = {"TradingAccountId": trading_acc_id, "OrderId": order_id}
        if market_id is not None:
            json_data["MarketId"] = market_id
        r = self.session.post(self.rest_url + api_url, json=json_data)
        resp = json.loads(r.text)

        return resp
