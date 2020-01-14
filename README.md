# gcapi-python
Python package for [Gain Capital API](http://docs.labs.gaincapital.com/) used for trading on [Forex.com](https://www.forex.com/en-ca/)

[![PyPI version](https://badge.fury.io/py/gcapi-python.svg)](https://badge.fury.io/py/gcapi-python)

## Table of Contents
* [Getting Started](#Getting-Started)
    * [Installation](#Installation)
    * [Usage](#Usage)
    * [Functions](#Functions)
        * [Account Information](#Account-Information)
        * [Margin Information](#Margin-Information)
        * [Market Information](#Market-Information)
        * [Pricing](#Pricing)
        * [Trading](#Trading)
* [Contact](#Contact)

## Getting Started

### Installation

```bash
pip install gcapi-python
```

### Usage
After installing, import into your project

```python
from gcapi import GCapiClient
```

Initialize with [Forex.com](https://www.forex.com/en-ca/) credentials and app key.

```python
api = GCapiClient(username='usr', password='***', appkey='***', proxies=None)
```

### Functions

#### Account Information

```python
api.get_account_info(get=None)
```

#### Margin Information

```python
api.get_margin_info(get=None)
```

#### Market Information

```python
api.get_market_info(market_name,get=None)
```

#### Pricing

```python
api.get_prices(market_id=None, num_ticks=None, from_ts=None, to_ts=None)
```

#### Trading

```python
api.trade_order(quantity, offer_price, direction, trading_acc_id=None, market_id=None, market_name=None, stop_loss=None, 
                take_profit=None, trigger_price=None)
```

## Contact
Please contact [**Kyu Mok (Ricky) Kim**](mailto:rickykim93@hotmail.com) if you have any questions, suggestions, or feedback.

Website: [rickykim.net](https://rickykim.net/)
