import requests
import json
import pandas as pd
from gcapi.gcapi_exception import GCapiException
from gcapi.gcapi_tools import format_date, check_interval, check_span

class GCapiClient:
	def __init__(self, username, password, appkey, proxies=None):
		self.rest_url = 'https://ciapi.cityindex.com/TradingAPI'
		headers = {'Content-Type': 'application/json'}
		data = {
			"UserName": username,
			"Password": password,
			"AppKey": appkey
		}
		r = requests.post(self.rest_url + '/session', headers=headers, proxies=proxies, json=data)
		resp = json.loads(r.text)
		if resp['StatusCode']!=1:
			raise GCapiException(resp)
		session = resp['Session']
		headers = {
			'Content-Type': 'application/json',
			'UserName': username,
			'Session': session
		}
		with requests.Session() as s:
			s.headers = headers
		if proxies is not None:
			s.proxies.update(proxies)
		self.session=s

	def get_account_info(self, get=None):
		"""
		Gets trading account general information
		:param get: retrieve specific information (e.g. TradingAccountId)
		:return: trading account information
		"""
		r=self.session.get(self.rest_url + '/UserAccount/ClientAndTradingAccount')
		resp = json.loads(r.text)
		try:
			self.trading_account_id = resp['TradingAccounts'][0]['TradingAccountId']
			if get is not None:
				return resp['TradingAccounts'][0][get]
			else:
				return resp
		except:
			raise GCapiException(resp)

	def get_margin_info(self, get=None):
		"""
		Gets trading account margin information
		:param get: retrieve specific information (e.g. Cash)
		:return: trading account margin information
		"""
		r = self.session.get(self.rest_url + '/margin/ClientAccountMargin')
		resp = json.loads(r.text)
		try:
			self.cash = resp['Cash']
			if get is not None:
				return resp[get]
			else:
				return resp
		except:
			raise GCapiException(resp)

	def get_market_info(self, market_name, get=None):
		"""
		Gets market information
		:param market_name: market name (e.g. USD/CAD)
		:param get: retrieve specific information (e.g. MarketId)
		:return: market information
		"""
		r = self.session.get(self.rest_url + f'/cfd/markets?MarketName={market_name}')
		resp = json.loads(r.text)
		try:
			self.market_name = market_name
			self.market_id = resp['Markets'][0]['MarketId']
			if get is not None:
				return resp['Markets'][0][get]
			else:
				return resp
		except:
			raise GCapiException(resp)

	def get_prices(self, market_id=None, num_ticks=None, from_ts=None, to_ts=None, price_type=None):
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
			price_type='MID'
		else:
			price_type=price_type.upper()
		if market_id is None:
			market_id = self.market_id
		if from_ts is not None and to_ts is not None:
			r = self.session.get(
				self.rest_url + f'/market/{market_id}/tickhistorybetween?fromTimeStampUTC={from_ts}&toTimestampUTC={to_ts}&priceType={price_type}')
		else:
			if not num_ticks:
				num_ticks=1
			if from_ts is not None:
				r = self.session.get(
					self.rest_url + f'/market/{market_id}/tickhistorybefore?maxResults={num_ticks}&toTimeStampUTC={to_ts}&priceType={price_type}')
			elif to_ts is not None:
				r = self.session.get(
					self.rest_url + f'/market/{market_id}/tickhistoryafter?maxResults={num_ticks}&fromTimeStampUTC={from_ts}&priceType={price_type}')
			else:
				r = self.session.get(self.rest_url + f'/market/{market_id}/tickhistory?PriceTicks={num_ticks}&priceType={price_type}')
		resp = json.loads(r.text)
		try:
			if num_ticks==1:
				return resp['PriceTicks'][0]['Price']
			else:
				return resp
		except:
			raise GCapiException(resp)

	def get_ohlc(self, market_id=None, num_ticks=None, interval="HOUR", span=1, from_ts=None, to_ts=None):
		"""
		Get the open, high, low, close of a specific market_id
		:param market_id: market ID
		:param num_ticks: number of price ticks/data to retrieve
		:param interval: MINUTE, HOUR or DAY tick interval
		:param span: it can be a combination of span with interval, 1Hour, 15 MINUTE
		:param from_ts: from timestamp UTC
		:param to_ts: to timestamp UTC
		:return: ohlc dataframe
		"""


		if market_id is None:
			market_id = self.market_id
		interval = check_interval(interval)
		span = check_span(interval, span)
		if from_ts is not None and to_ts is not None:
			r = self.session.get(
				self.rest_url + f'/market/{market_id}/barhistorybetween?interval={interval}&span={span}&fromTimeStampUTC={from_ts}&toTimestampUTC={to_ts}')
		else:
			if not num_ticks:
				num_ticks=1
			if from_ts is not None:
				r = self.session.get(
					self.rest_url + f'/market/{market_id}/barhistorybefore?interval={interval}&span={span}&maxResults={num_ticks}&toTimeStampUTC={to_ts}')
			elif to_ts is not None:
				r = self.session.get(
					self.rest_url + f'/market/{market_id}/tickhistoryafter?interval={interval}&span={span}&maxResults={num_ticks}&fromTimeStampUTC={from_ts}')
			else:
				r = self.session.get(self.rest_url + f'/market/{market_id}/barhistory?interval={interval}&span={span}&PriceBars={num_ticks}')
		resp = json.loads(r.text)

		try:
			if num_ticks==1:
				return resp.get('PriceBars')[0]
			else:
				df_ohlc = pd.DataFrame(resp.get('PriceBars'))
				df_ohlc['BarDate'] = df_ohlc['BarDate'].map(format_date)
				return df_ohlc
		except:
			raise GCapiException(resp)


	def trade_order(self, quantity, offer_price, direction, trading_acc_id=None, market_id=None, market_name=None, stop_loss=None,
					take_profit=None, trigger_price=None):
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
		:return:
		"""
		if trading_acc_id is None:
			trading_acc_id = self.trading_account_id
		if market_id is None:
			market_id = self.market_id
		if market_name is None:
			market_name = self.market_name
		api_url="/order/newtradeorder"
		direction=direction.lower()
		if direction=='buy':
			opp_direction='sell'
		elif direction=='sell':
			opp_direction='buy'
		else:
			raise ValueError('Please provide buy or sell for direction')
		trade_details = {
			"Direction": direction,
			"MarketId": market_id,
			"Quantity": quantity,
			"MarketName": market_name,
			'TradingAccountId': trading_acc_id,
			"OfferPrice": offer_price
		}
		if trigger_price is not None:
			trade_details['TriggerPrice']=trigger_price
			api_url="/order/newstoplimitorder"
		ifdone = {}
		if stop_loss:
			ifdone['Stop'] = {'TriggerPrice': stop_loss, "Direction": opp_direction, 'Quantity': quantity}
		if take_profit:
			ifdone['Limit'] = {'TriggerPrice': take_profit, "Direction": opp_direction, 'Quantity': quantity}
		if len(ifdone):
			trade_details['IfDone'] = [ifdone]
		r = self.session.post(self.rest_url + api_url, json=trade_details)
		resp = json.loads(r.text)
		return resp

	def list_open_positions(self, trading_acc_id=None):
		if trading_acc_id is None:
			trading_acc_id = self.trading_account_id
		api_url=f"/order/openpositions?TradingAccountId={trading_acc_id}"
		r = self.session.get(self.rest_url + api_url)
		resp = json.loads(r.text)
		return resp
