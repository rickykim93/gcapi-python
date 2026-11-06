"""Shared fixtures and realistic sample payloads for the mocked gcapi test suite.

No test touches the network: every HTTP call goes through a `responses.RequestsMock`
that fails on any unregistered URL.

Sample payloads follow the shapes the Gain Capital / City Index CIAPI returns
(ApiLogOnResponseDTO, ApiErrorResponseDTO, GetPriceBarResponseDTO, ...). Timestamps
use the API's `/Date(<epoch-ms>)/` format and are chosen to land exactly on
00:00 UTC so that timezone bugs are visible.
"""

import copy
import json
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

import pytest
import responses

from gcapi import GCapiClient

BASE = "https://ciapi.cityindex.com/TradingAPI"

USERNAME = "DM123456"
PASSWORD = "hunter2"
APPKEY = "test-app-key"
SESSION_ID = "5998f6b1-8f3c-4b2e-9a71-0d6c2e6f4a10"

CLIENT_ACCOUNT_ID = 400100001
TRADING_ACCOUNT_ID = 400200002
MARKET_ID = 401484317
MARKET_NAME = "USD/CAD"

# 2023-03-06 .. 2023-03-10, each at 00:00:00 UTC (epoch milliseconds)
DAY_MS = [1678060800000, 1678147200000, 1678233600000, 1678320000000, 1678406400000]


def _date(ms):
    return f"/Date({ms})/"


SAMPLES = {
    # POST /session -- success
    "login_ok": {
        "Session": SESSION_ID,
        "PasswordChangeRequired": False,
        "AllowedAccountOperator": False,
        "StatusCode": 1,
        "Is2FAEnabled": False,
        "TwoFAToken": None,
        "Additional2FAMethods": None,
    },
    # POST /session -- HTTP 200 but a non-success StatusCode
    "login_bad_status": {
        "Session": None,
        "PasswordChangeRequired": True,
        "AllowedAccountOperator": False,
        "StatusCode": 2,
        "Is2FAEnabled": False,
        "TwoFAToken": None,
        "Additional2FAMethods": None,
    },
    # POST /session -- HTTP 401, ApiErrorResponseDTO (no StatusCode key)
    "login_error_dto": {
        "HttpStatus": 401,
        "ErrorMessage": "Sorry, your login has failed. This may be because your username or password is incorrect.",
        "ErrorCode": 4010,
    },
    # GET /UserAccount/ClientAndTradingAccount
    "account": {
        "LogonUserName": USERNAME,
        "ClientAccountId": CLIENT_ACCOUNT_ID,
        "CultureId": 69,
        "ClientAccountCurrency": "USD",
        "AccountOperatorId": 3321,
        "TradingAccounts": [
            {
                "TradingAccountId": TRADING_ACCOUNT_ID,
                "TradingAccountCode": "DM123456",
                "TradingAccountStatus": "Open",
                "TradingAccountType": "Spread Betting",
            }
        ],
        "PersonalEmailAddress": "trader@example.com",
        "HasMultipleEmailAddresses": False,
        "AccountHolders": [{"LegalPartyId": 5550001, "Name": "Test Trader"}],
        "ClientTypeId": 1,
        "LinkedClientAccounts": [],
        "IsNewUser": False,
        "IsPilotUser": False,
        "IsFifo": True,
    },
    # GET /margin/ClientAccountMargin
    "margin": {
        "Cash": 10000.0,
        "Margin": 412.37,
        "MarginIndicator": 4.12,
        "NetEquity": 10023.5,
        "OpenTradeEquity": 23.5,
        "TradeableFunds": 9611.13,
        "PendingFunds": 0.0,
        "TradingResource": 10023.5,
        "TotalMarginRequirement": 412.37,
        "CurrencyId": 11,
        "CurrencyISO": "USD",
    },
    # GET /cfd/markets?MarketName=USD/CAD
    "markets": {"Markets": [{"MarketId": MARKET_ID, "Name": MARKET_NAME}]},
    "markets_empty": {"Markets": []},
    # GET /market/{id}/tickhistory*
    "ticks": {
        "PriceTicks": [
            {"TickDate": _date(1678406400000), "Price": 1.37865},
            {"TickDate": _date(1678406401000), "Price": 1.37871},
            {"TickDate": _date(1678406403000), "Price": 1.37868},
        ]
    },
    # GET /market/{id}/barhistory* -- complete bars plus the still-forming bar
    "bars": {
        "PriceBars": [
            {"BarDate": _date(DAY_MS[0]), "Open": 43.825, "High": 44.675, "Low": 43.475, "Close": 43.535},
            {"BarDate": _date(DAY_MS[1]), "Open": 43.545, "High": 43.805, "Low": 42.275, "Close": 42.445},
            {"BarDate": _date(DAY_MS[2]), "Open": 42.570, "High": 43.035, "Low": 42.035, "Close": 42.885},
            {"BarDate": _date(DAY_MS[3]), "Open": 43.015, "High": 43.745, "Low": 41.115, "Close": 41.315},
        ],
        "PartialPriceBar": {
            "BarDate": _date(DAY_MS[4]),
            "Open": 41.375,
            "High": 41.825,
            "Low": 39.885,
            "Close": 40.185,
        },
    },
    # POST /order/newtradeorder and /order/newstoplimitorder
    "trade_ok": {
        "Status": 1,
        "StatusReason": 1,
        "OrderId": 654321987,
        "Orders": [],
        "Quote": None,
        "Actions": [],
        "ErrorMessage": None,
    },
    # GET /order/openpositions
    "open_positions": {
        "OpenPositions": [
            {
                "OrderId": 654321987,
                "MarketId": MARKET_ID,
                "MarketName": MARKET_NAME,
                "Direction": "buy",
                "Quantity": 1000.0,
                "Price": 1.37871,
                "TradingAccountId": TRADING_ACCOUNT_ID,
                "Currency": "CAD",
                "Status": 3,
                "StopOrder": None,
                "LimitOrder": None,
                "LastChangedDateTimeUTC": _date(1678406403000),
                "CreatedDateTimeUTC": _date(1678406403000),
            }
        ]
    },
    # POST /order/activeorders
    "active_orders": {
        "ActiveOrders": [
            {
                "TypeId": 2,
                "TradeOrder": None,
                "StopLimitOrder": {
                    "OrderId": 654322001,
                    "MarketId": MARKET_ID,
                    "Direction": "sell",
                    "Quantity": 1000.0,
                    "TriggerPrice": 1.36500,
                    "TradingAccountId": TRADING_ACCOUNT_ID,
                    "Status": 2,
                },
            }
        ]
    },
    # POST /order/cancel
    "cancel_ok": {"OrderId": 654322001, "Status": 4, "StatusReason": 1},
    # Generic ApiErrorResponseDTO with every field populated
    "error_full": {
        "StatusCode": 3,
        "HttpStatus": 400,
        "ErrorMessage": "Market is closed",
        "ErrorCode": 4000,
        "AdditionalInfo": "MarketId 401484317",
    },
}


@pytest.fixture
def samples():
    """Fresh deep copy of every sample payload, so tests can mutate freely."""
    return copy.deepcopy(SAMPLES)


@pytest.fixture
def rsps():
    """Active responses mock. Unregistered URLs raise ConnectionError."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock


@pytest.fixture
def login(rsps, samples):
    """Register a successful POST /session."""
    return rsps.post(f"{BASE}/session", json=samples["login_ok"])


@pytest.fixture
def client(rsps, login):
    """A logged-in GCapiClient with no account/market state loaded yet.
    The login call is cleared from rsps.calls."""
    api = GCapiClient(username=USERNAME, password=PASSWORD, appkey=APPKEY)
    rsps.calls.reset()
    return api


@pytest.fixture
def api(rsps, client, samples):
    """A logged-in client whose account and market state were loaded through the
    real get_account_info / get_market_info calls (as a user would). The calls
    are cleared from rsps.calls so each test sees only its own requests."""
    rsps.get(f"{BASE}/UserAccount/ClientAndTradingAccount", json=samples["account"])
    rsps.get(f"{BASE}/cfd/markets", json=samples["markets"])
    client.get_account_info()
    client.get_market_info(MARKET_NAME)
    rsps.calls.reset()
    return client


@pytest.fixture
def sent(rsps):
    """sent(i=-1) -> the i-th recorded request, broken into comparable parts:
    method, full url, path, params (dict of query string), json body, headers."""

    def _sent(i=-1):
        req = rsps.calls[i].request
        parts = urlsplit(req.url)
        body = req.body
        if isinstance(body, bytes):
            body = body.decode()
        return SimpleNamespace(
            method=req.method,
            url=req.url,
            path=parts.path,
            params=dict(parse_qsl(parts.query, keep_blank_values=True)),
            json=json.loads(body) if body else None,
            headers=req.headers,
        )

    return _sent
