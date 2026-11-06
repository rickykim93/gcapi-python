"""Login / session setup in GCapiClient.__init__."""

import pytest
import requests

from gcapi import GCapiClient
from gcapi.gcapi_exception import GCapiException
from tests.conftest import APPKEY, BASE, PASSWORD, SESSION_ID, USERNAME


def test_login_posts_credentials_to_session_endpoint(rsps, login, sent):
    GCapiClient(username=USERNAME, password=PASSWORD, appkey=APPKEY)

    req = sent(0)
    assert req.method == "POST"
    assert req.url == f"{BASE}/session"
    assert req.json == {"UserName": USERNAME, "Password": PASSWORD, "AppKey": APPKEY}
    assert req.headers["Content-Type"] == "application/json"


def test_login_stores_session_id_and_username(client):
    assert client.session_id == SESSION_ID
    assert client.username == USERNAME


def test_subsequent_requests_carry_session_headers(rsps, client, samples, sent):
    rsps.get(f"{BASE}/margin/ClientAccountMargin", json=samples["margin"])
    client.get_margin_info()

    headers = sent().headers
    assert headers["UserName"] == USERNAME
    assert headers["Session"] == SESSION_ID
    assert headers["Content-Type"] == "application/json"


def test_proxies_are_applied_to_session(rsps, login):
    proxies = {"https": "http://proxy.example.com:8080"}
    api = GCapiClient(username=USERNAME, password=PASSWORD, appkey=APPKEY, proxies=proxies)
    assert api.session.proxies["https"] == "http://proxy.example.com:8080"


def test_login_non_success_status_code_raises(rsps, samples):
    rsps.post(f"{BASE}/session", json=samples["login_bad_status"])
    with pytest.raises(GCapiException) as exc:
        GCapiClient(username=USERNAME, password=PASSWORD, appkey=APPKEY)
    assert exc.value.get_status_code() == 2


def test_login_error_dto_raises_gcapi_exception(rsps, samples):
    rsps.post(f"{BASE}/session", json=samples["login_error_dto"], status=401)
    with pytest.raises(GCapiException) as exc:
        GCapiClient(username=USERNAME, password=PASSWORD, appkey=APPKEY)
    assert exc.value.get_error_code() == 4010
    assert exc.value.get_http_status() == 401
    assert exc.value.get_status_code() is None


def test_session_is_not_closed_during_init(rsps, login, monkeypatch):
    closed = []
    original_close = requests.Session.close

    def spy_close(self):
        closed.append(self)
        original_close(self)

    monkeypatch.setattr(requests.Session, "close", spy_close)
    api = GCapiClient(username=USERNAME, password=PASSWORD, appkey=APPKEY)
    assert not any(s is api.session for s in closed)
