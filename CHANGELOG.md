# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### ⚠️ Breaking changes

- **Dates are now timezone-aware UTC** ([#10]). `gcapi.gcapi_tools.format_date` returns a
  `datetime` with `tzinfo=timezone.utc`, and the `BarDate` column from `get_ohlc` is
  `datetime64[ns, UTC]`. They used to be naive datetimes in the *machine's local time*, which put
  bars on the wrong date for anyone outside UTC. Code that compares these values with naive
  datetimes will raise `TypeError` or compare incorrectly. To migrate:

  ```python
  df["BarDate"].dt.tz_convert("America/New_York")  # view in another timezone
  df["BarDate"].dt.tz_localize(None)  # back to naive (UTC) if you must
  ```

- **Python 3.10+ is required.**
- `get_prices` / `get_ohlc` called with *only* `from_ts` or *only* `to_ts` now query the right
  direction (see Fixed). If you relied on the old, swapped results, swap your arguments back.

### Added

- `update_trade()` to update an existing trade, e.g. to add or move its stop loss / take profit.
  Thanks to **clemstar** ([#13]).
- `trade_order(..., bid_price=None, price_tolerance=None)`: send `BidPrice` (needed for some
  sell/stop orders) and `PriceTolerance` (acceptable slippage). Both are new keyword arguments at
  the end, and the existing argument order is unchanged. Thanks to **clemstar** ([#13]).
- `cancel_order(..., market_id=None)`: sends `MarketId`, which the API now requires. It defaults to
  the market loaded by `get_market_info()`. Thanks to **clemstar** ([#13]).
- `get_ohlc(..., include_partial=False)`: pass `True` to append the still-forming bar (the API's
  `PartialPriceBar`) as the last row ([#10]).
- Streaming prices via Lightstreamer (`init_streaming_client()`), `list_active_orders()` and
  `cancel_order()`. Thanks to **Andrew Drogalis** ([#8], [#9]). Merged after 0.0.9 and first
  released here.
- Type hints on the public API and a `py.typed` marker.
- `GCapiClient` exported via `__all__`; `str(GCapiException)` now shows the error payload.
- A mocked test suite, `[test]` and `[dev]` extras, ruff linting/formatting, and GitHub Actions CI
  on Python 3.10–3.13.

### Fixed

- `format_date` / `BarDate` converted UTC timestamps to local time ([#10]).
- `get_ohlc` dropped the most recent, still-forming bar, so the latest daily bar looked missing
  ([#10]). It is now available through `include_partial=True`.
- `get_prices` with only `from_ts` called `tickhistorybefore` with `toTimeStampUTC=None`, and with
  only `to_ts` called `tickhistoryafter` with `fromTimeStampUTC=None`.
- `get_ohlc` had the same swap, and its "after" branch called the tick endpoint
  `tickhistoryafter` instead of `barhistoryafter`.
- `check_span` reset every span to 1, so `get_ohlc(span=...)` was always ignored.
- `list_active_orders` and `cancel_order` ignored the `trading_acc_id` argument.
- A failed login (HTTP 401) raised `KeyError` instead of `GCapiException`, and the
  `GCapiException` getters raised `KeyError` for fields missing from the error response. They now
  return `None`.
- The `requests.Session` was closed during `__init__` by a `with` block.
- `GCapiException` is now raised with the original error chained (`raise ... from err`).
- The wheel no longer installs a top-level `tests` package.
- Examples: `technical_indicators.py` uses the library's UTC dates and the 17:00 New York trading-day
  boundary instead of local time, and `streaming_example.py` no longer logs in or loops forever when
  imported.

### Changed

- Packaging moved from `setup.py` to `pyproject.toml` (hatchling).
- README: removed the dead `docs.labs.gaincapital.com` / `faq.labs.gaincapital.com` links ([#11]),
  documented the new options, and added "Running tests" and "Getting a demo account and API key".

## [0.0.9] - 2021-02-14

- Minor typo fix (#7).

Earlier releases (0.0.1–0.0.8, 2020–2021) are listed on
[PyPI](https://pypi.org/project/gcapi-python/#history).

[0.1.0]: https://github.com/rickykim93/gcapi-python/compare/v0.0.9...HEAD
[0.0.9]: https://github.com/rickykim93/gcapi-python/releases/tag/v0.0.9
[#8]: https://github.com/rickykim93/gcapi-python/pull/8
[#9]: https://github.com/rickykim93/gcapi-python/pull/9
[#10]: https://github.com/rickykim93/gcapi-python/issues/10
[#11]: https://github.com/rickykim93/gcapi-python/issues/11
[#13]: https://github.com/rickykim93/gcapi-python/pull/13
