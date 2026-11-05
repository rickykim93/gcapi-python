"""get_account_info, get_margin_info, get_market_info."""
import pytest

from gcapi.gcapi_exception import GCapiException
from tests.conftest import BASE, MARKET_ID, MARKET_NAME, TRADING_ACCOUNT_ID

ACCOUNT_URL = f"{BASE}/UserAccount/ClientAndTradingAccount"
MARGIN_URL = f"{BASE}/margin/ClientAccountMargin"
MARKETS_URL = f"{BASE}/cfd/markets"


# --- account -----------------------------------------------------------------

def test_get_account_info_returns_full_response(rsps, client, samples, sent):
    rsps.get(ACCOUNT_URL, json=samples["account"])

    assert client.get_account_info() == samples["account"]
    assert sent().method == "GET"
    assert sent().url == ACCOUNT_URL


def test_get_account_info_stores_trading_account_id(rsps, client, samples):
    rsps.get(ACCOUNT_URL, json=samples["account"])
    client.get_account_info()
    assert client.trading_account_id == TRADING_ACCOUNT_ID


def test_get_account_info_get_returns_first_trading_account_field(rsps, client, samples):
    rsps.get(ACCOUNT_URL, json=samples["account"])
    assert client.get_account_info(get="TradingAccountCode") == "DM123456"


def test_get_account_info_error_raises(rsps, client, samples):
    rsps.get(ACCOUNT_URL, json=samples["error_full"], status=400)
    with pytest.raises(GCapiException) as exc:
        client.get_account_info()
    assert exc.value.get_error_message() == "Market is closed"


# --- margin ------------------------------------------------------------------

def test_get_margin_info_returns_full_response(rsps, client, samples, sent):
    rsps.get(MARGIN_URL, json=samples["margin"])

    assert client.get_margin_info() == samples["margin"]
    assert sent().method == "GET"
    assert sent().url == MARGIN_URL


def test_get_margin_info_stores_cash(rsps, client, samples):
    rsps.get(MARGIN_URL, json=samples["margin"])
    client.get_margin_info()
    assert client.cash == 10000.0


def test_get_margin_info_get_returns_field(rsps, client, samples):
    rsps.get(MARGIN_URL, json=samples["margin"])
    assert client.get_margin_info(get="NetEquity") == 10023.5


def test_get_margin_info_error_raises(rsps, client, samples):
    rsps.get(MARGIN_URL, json=samples["error_full"], status=400)
    with pytest.raises(GCapiException):
        client.get_margin_info()


# --- market info -------------------------------------------------------------

def test_get_market_info_queries_by_name(rsps, client, samples, sent):
    rsps.get(MARKETS_URL, json=samples["markets"])

    assert client.get_market_info(MARKET_NAME) == samples["markets"]
    assert sent().method == "GET"
    assert sent().url == f"{MARKETS_URL}?MarketName=USD/CAD"


def test_get_market_info_stores_market_id_and_name(rsps, client, samples):
    rsps.get(MARKETS_URL, json=samples["markets"])
    client.get_market_info(MARKET_NAME)
    assert client.market_id == MARKET_ID
    assert client.market_name == MARKET_NAME


def test_get_market_info_get_returns_first_market_field(rsps, client, samples):
    rsps.get(MARKETS_URL, json=samples["markets"])
    assert client.get_market_info(MARKET_NAME, get="MarketId") == MARKET_ID


def test_get_market_info_unknown_market_raises(rsps, client, samples):
    rsps.get(MARKETS_URL, json=samples["markets_empty"])
    with pytest.raises(GCapiException):
        client.get_market_info("NOT/AMARKET")
