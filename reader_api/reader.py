import json
import time

import pandas as pd
from binance.client import Client

import client_config
from utils.constants import Params


class Reader:
    def __init__(self, logger):
        self._client = Client(client_config.api_key, client_config.api_security)
        self.logger = logger

    @staticmethod
    def get_times_for_trades():
        end_time = round(time.time() * 1000)
        start_time = end_time - (60 * 1000)
        return start_time, end_time

    def get_spot_balance(self, coin):
        assets = self._client.get_asset_balance(coin)
        return assets['free']

    def get_trades(self, first_currency, second_currency):
        start_time, end_time = self.get_times_for_trades()
        params = {Params.SYMBOL: f"{first_currency}{second_currency}",
                  Params.START_TIME: start_time, Params.END_TIME: end_time}
        btc_trades = json.dumps(self._client.get_aggregate_trades(**params))
        return pd.read_json(btc_trades)

    def get_tickers(self):
        return self._client.get_all_tickers()

    def get_order_info(self, symbol, orderId):
        return self._client.get_order(symbol=symbol, orderId=orderId)

    def get_my_trades(self, symbol):
        return self._client.get_my_trades(symbol=symbol)

    def create_order(self, symbol, side, order_type, quantity, price, timeInForce):
        if price is None:
            return self._client.create_order(symbol=symbol, side=side, type=order_type,
                                                     timeInForce=timeInForce, quantity=quantity)
        else:
            return self._client.create_order(symbol=symbol, side=side, type=order_type,
                                         timeInForce=timeInForce, quantity=quantity, price=price)

    def get_price(self, symbol):
        tickers = self.get_tickers()
        for ticker in tickers:
            if ticker['symbol'] == symbol:
                return ticker['price']