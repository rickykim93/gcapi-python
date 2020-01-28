from datetime import datetime, timedelta
import pandas as pd
import re
import time

def calc_rsi(series, n=14):
	"""
	Returns RSI value given series of prices
	:param series: series of prices
	:param n: number of periods to calculate the initial RSI value
	:return: RSI
	"""
	delta = series.diff()
	dUp, dDown = delta.copy(), delta.copy()
	dUp[dUp < 0] = 0
	dDown[dDown > 0] = 0
	RolUp = dUp.rolling(n).mean()
	RolDown = dDown.rolling(n).mean().abs()
	RS = RolUp / RolDown
	rsi= 100.0 - (100.0 / (1.0 + RS))
	return rsi

def convert_date(x):
	"""
	Converts UTC to datetime and vice versa
	:param x: UTC or datetime
	:return: datetime or UTC
	"""
	if type(x)==datetime:
		return int(x.timestamp())
	else:
		return datetime.fromtimestamp(int(re.search('\d+', x).group()) / 1000)

def calc_hourly_rsi(api, market_id, n=14):
	"""
	Calculates hourly RSI
	:param api: GCapiClient
	:param market_id: market ID
	:param n: number of periods to calculate initial RSI value
	:return: RSI
	"""
	prices = []
	time=None
	for h in range(n + 1):
		if h == 0:
			resp = api.get_prices(market_id, num_ticks=2)
		else:
			time=convert_date(convert_date(time)-timedelta(hours=1))
			resp = api.get_prices(market_id, num_ticks=2, to_ts=time)
		time = resp['PriceTicks'][-1]['TickDate']
		prices.append(float(resp['PriceTicks'][-1]['Price']))
	return calc_rsi(pd.Series(reversed(prices))).iloc[-1]

def calc_5m_ema(api, market_id):
	"""
	Calculate 5 minute exponential moving average (EMA)
	:param api: GCapiClient
	:param market_id: market ID
	:return: 8, 13, 21 5-minute EMAs
	"""
	prices = []
	time = None
	for h in range(21*2 + 1):
		if h == 0:
			resp=api.get_prices(market_id, num_ticks=2)
		else:
			time = convert_date(convert_date(time) - timedelta(minutes=5))
			resp=api.get_prices(market_id, num_ticks=2, to_ts=time)
		time = resp['PriceTicks'][-1]['TickDate']
		prices.append(float(resp['PriceTicks'][-1]['Price']))
	prices = list(reversed(prices))
	return pd.Series(prices).ewm(span=8, adjust=False).mean().iloc[-1], \
		   pd.Series(prices).ewm(span=13, adjust=False).mean().iloc[-1], \
		   pd.Series(prices).ewm(span=21, adjust=False).mean().iloc[-1]

def calc_pivot(api, market_id):
	"""
	Calculate Pivot points for Support and Resistance Levels
	:param api: GCapiClient
	:param market_id: market ID
	:return: Returns dictionary of support and resistance levels
	"""
	now=datetime.now()
	if now.hour>=17:
		if now.weekday() == 6:  # sunday
			from_ts = convert_date((datetime.now() - timedelta(days=3)).replace(hour=17, minute=0, second=0))
			to_ts = convert_date((datetime.now() - timedelta(days=2)).replace(hour=17, minute=0, second=0))
		else:
			from_ts=convert_date((datetime.now()-timedelta(days=1)).replace(hour=17, minute=0, second=0))
			to_ts=convert_date(datetime.now().replace(hour=17, minute=0, second=0))
	else:
		if now.weekday()==0:  # monday
			from_ts=convert_date((datetime.now()-timedelta(days=4)).replace(hour=17, minute=0, second=0))
			to_ts=convert_date((datetime.now()-timedelta(days=3)).replace(hour=17, minute=0, second=0))
		else:
			from_ts=convert_date((datetime.now()-timedelta(days=2)).replace(hour=17, minute=0, second=0))
			to_ts=convert_date((datetime.now()-timedelta(days=1)).replace(hour=17, minute=0, second=0))
	resp=api.get_prices(market_id, from_ts=from_ts, to_ts=to_ts)
	time.sleep(0.3)
	df = pd.DataFrame(resp['PriceTicks'])
	high = df['Price'].max()
	low = df['Price'].min()
	close = df['Price'].iloc[-1]
	SnR={}
	SnR['PP']=(high+low+close)/3
	SnR['R1']=(2*SnR['PP'])-low
	SnR['S1']=(2*SnR['PP'])-high
	SnR['R2']=SnR['PP']+(high-low)
	SnR['S2']=SnR['PP']-(high-low)
	SnR['R3']=high+2*(SnR['PP']-low)
	SnR['S3']=low-2*(high-SnR['PP'])
	return SnR
