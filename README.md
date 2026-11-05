# gcapi-python

[![CI](https://github.com/rickykim93/gcapi-python/actions/workflows/ci.yml/badge.svg)](https://github.com/rickykim93/gcapi-python/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/gcapi-python)](https://pypi.org/project/gcapi-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/gcapi-python)](https://pypi.org/project/gcapi-python/)

Unofficial Python client for the Gain Capital REST API
(`https://ciapi.cityindex.com/TradingAPI`) used for trading on [FOREX.com](https://www.forex.com/).

## Table of Contents
* [Getting Started](#getting-started)
    * [Installation](#installation)
    * [Getting a demo account and API key](#getting-a-demo-account-and-api-key)
    * [Usage](#usage)
* [Endpoints](#endpoints)
    * [Account Information](#account-information)
    * [Margin Information](#margin-information)
    * [Market Information](#market-information)
    * [Pricing](#pricing)
    * [Trading](#trading)
    * [Orders and Positions](#orders-and-positions)
    * [Streaming](#streaming)
    * [Errors](#errors)
* [Examples](#examples)
* [Running tests](#running-tests)
* [Contact](#contact)

## Getting Started

### Installation

Requires Python 3.10 or newer.

```bash
pip install gcapi-python
```

### Getting a demo account and API key

You need three things to log in: your FOREX.com username, your password, and an **AppKey**.

1. Open a demo (practice) or live account at [FOREX.com](https://www.forex.com/).
2. Contact FOREX.com's support team and ask for REST API access on that account. They enable it and
   give you the AppKey. It can take a few working days.

Try things out on a demo account before trading real money. This is an unofficial library, and
FOREX.com may change its API access process, so check with them if these steps no longer work.

### Usage

```python
from gcapi import GCapiClient

api = GCapiClient(username="usr", password="***", appkey="***", proxies=None)

api.get_account_info()  # loads and stores your trading account ID
api.get_market_info("USD/CAD")  # loads and stores the market ID and name
```

Most methods fall back to the trading account and market loaded by `get_account_info()` and
`get_market_info()`, so you only need to pass `trading_acc_id` / `market_id` to override them.

All timestamps you pass (`from_ts`, `to_ts`) are Unix timestamps in seconds (UTC). Dates the library
returns are **timezone-aware UTC** `datetime`s.

## Endpoints

### Account Information

```python
api.get_account_info(get=None)  # get="TradingAccountId" returns a single field
```

### Margin Information

```python
api.get_margin_info(get=None)  # get="Cash" returns a single field
```

### Market Information

```python
api.get_market_info(market_name, get=None)  # get="MarketId" returns a single field
```

### Pricing

Tick prices:

```python
api.get_prices(market_id=None, num_ticks=None, from_ts=None, to_ts=None, price_type=None)
```

* No timestamps: the latest `num_ticks` ticks. With `num_ticks` unset this returns only the latest price.
* `from_ts` only: `num_ticks` ticks after `from_ts`.
* `to_ts` only: `num_ticks` ticks before `to_ts`.
* Both: all ticks between them.
* `price_type`: `"MID"` (default), `"BID"` or `"ASK"`.

OHLC bars as a pandas DataFrame:

```python
api.get_ohlc(
    market_id=None,
    num_ticks=None,
    interval="HOUR",
    span=1,
    from_ts=None,
    to_ts=None,
    include_partial=False,
)
```

* `interval`: `"MINUTE"`, `"HOUR"`, `"DAY"`, `"WEEK"` or `"MONTH"`.
* `span`: bar size within the interval. `MINUTE` allows 1, 2, 3, 5, 10, 15, 30 and `HOUR` allows 1, 2, 4, 8.
  Anything else, or any interval of a day or longer, uses 1.
* `from_ts` / `to_ts` work like `get_prices`.
* The `BarDate` column is timezone-aware UTC (`datetime64[ns, UTC]`). Use
  `df["BarDate"].dt.tz_convert("America/New_York")` to view it in another timezone.
* `include_partial`: the API returns completed bars separately from the bar that is still forming
  (for example today's daily bar). By default only completed bars are returned. Pass
  `include_partial=True` to append the forming bar as the last row. It has no effect when
  `num_ticks=1`, which returns the single latest completed bar as a dict.

```python
daily = api.get_ohlc(num_ticks=20, interval="DAY", include_partial=True)
```

### Trading

Place a market order, or a stop/limit order when `trigger_price` is given:

```python
api.trade_order(
    quantity,
    offer_price,
    direction,
    trading_acc_id=None,
    market_id=None,
    market_name=None,
    stop_loss=None,
    take_profit=None,
    trigger_price=None,
    bid_price=None,
    price_tolerance=None,
)
```

* `direction`: `"buy"` or `"sell"`.
* `stop_loss` / `take_profit`: attach stop and limit orders to the trade, closing it in the opposite direction.
* `bid_price`: the current bid. The API needs it for some sell and stop orders. Only sent if given.
* `price_tolerance`: the slippage you'll accept, in price points (`0` is allowed). Only sent if given.

Update an existing trade, for example to add or move its stop loss / take profit:

```python
api.update_trade(
    order_id,
    quantity,
    direction,
    offer_price=None,
    bid_price=None,
    trading_acc_id=None,
    market_id=None,
    market_name=None,
    stop_loss=None,
    take_profit=None,
    price_tolerance=None,
)
```

`direction` is the direction of the original trade. `offer_price`, `bid_price` and `price_tolerance`
are only sent if given.

### Orders and Positions

```python
api.list_open_positions(trading_acc_id=None)
api.list_active_orders(trading_acc_id=None)
api.cancel_order(order_id, trading_acc_id=None, market_id=None)
```

`cancel_order` sends the order's `MarketId`, which the API requires. It defaults to the market loaded
by `get_market_info()`.

### Streaming

Live prices via Lightstreamer:

```python
stream = api.init_streaming_client()
stream.subscribe_to_streaming(market_id_list=[401484317])
stream.real_time_snapshot()  # latest Bid/Offer/TickDate per market
stream.add_event_listener(print)  # or get called on every update
stream.unsubscribe_to_streaming()
```

### Errors

API errors raise `gcapi.gcapi_exception.GCapiException`:

```python
from gcapi.gcapi_exception import GCapiException

try:
    api.get_market_info("NOT/AMARKET")
except GCapiException as e:
    print(e.get_http_status(), e.get_error_code(), e.get_error_message())
```

Getters return `None` for fields the error response doesn't include.

## Examples

See the [examples](https://github.com/rickykim93/gcapi-python/tree/master/examples) folder:

* `technical_indicators.py`: RSI, EMA and pivot points from price data.
* `streaming_example.py`: streams live prices. Reads credentials from `GCAPI_USERNAME`,
  `GCAPI_PASSWORD` and `GCAPI_APPKEY`.

## Running tests

The test suite mocks every HTTP call with [`responses`](https://github.com/getsentry/responses), so it
needs no credentials or network access.

```bash
git clone https://github.com/rickykim93/gcapi-python.git
cd gcapi-python
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"          # pytest, responses, pytest-cov, ruff

pytest --cov                     # tests + coverage (fails below the threshold in pyproject.toml)
ruff check . && ruff format --check .
```

CI runs the same checks on Python 3.10–3.13 for every push and pull request.

## Contact

Please contact [**Kyu Mok (Ricky) Kim**](mailto:rickykim93@hotmail.com) if you have any questions,
suggestions, or feedback. Bug reports and pull requests are welcome on
[GitHub](https://github.com/rickykim93/gcapi-python/issues).

Gain Capital's old developer documentation and FAQ sites (`docs.labs.gaincapital.com`,
`faq.labs.gaincapital.com`) are no longer available. For questions about your account or API
access, contact FOREX.com support.

Website: [rickykim.net](https://rickykim.net/)
