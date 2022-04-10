from src.utils.constants import Coins
from src.utils.functions import current_milli_time


class Trader:
    def __init__(self, logger, reader, calculator):
        self.logger = logger
        self.reader = reader
        self.calculator = calculator

    def order_filled(self, order_info, waiting_time):
        waiting_time = waiting_time * 60 * 1000  # ms
        time_delta = 0
        max_sell_time_start = current_milli_time()
        while time_delta < waiting_time:
            symbol = order_info['symbol']
            order_info = self.reader.get_order_info(symbol=symbol, orderId=order_info['orderId'])
            if self.calculator.check_order_status(order_info, 'FILLED'):
                return True
            time_delta = current_milli_time() - max_sell_time_start
        return False

    def order_asset(self, symbol, side, order_type, quantity, price, time_in_force):
        order = self.reader.create_order(symbol=symbol, side=side, order_type=order_type, quantity=round(quantity, 8),
                                         price=round(price, 8), timeInForce=time_in_force)
        order_info = self.reader.get_order_info(symbol=symbol, orderId=order['orderId'])
        self.logger(f'order info: {order_info}')
        return order_info

    def buy_max_asset(self, asset, qty, price):
        symbol = asset + Coins.USDT
        return self.order_asset(symbol, 'BUY', 'LIMIT', qty, price, 'FOK')

    def sell_max_asset(self, asset, qty, price):
        symbol = asset + Coins.BTC
        return self.order_asset(symbol, 'SELL', 'LIMIT', qty, price, 'GTC')

    def return_max_usdt(self, order_info, asset):
        qty = order_info['origQty']
        symbol = asset + Coins.USDT

        # 3.2.4.a
        waiting_time = 2  # 2min
        if not self.order_filled(order_info, waiting_time):
            self.reader.cancel_order(order_info)
            price = float(order_info['price']) * 1.0015
            order_sell_limit_asset_usdt = self.order_asset(symbol, 'SELL', 'LIMIT', qty, price, 'GTC')

            # 3.2.4.b
            waiting_time = 3  # 3min
            if not self.order_filled(order_sell_limit_asset_usdt, waiting_time):
                self.reader.cancel_order(order_sell_limit_asset_usdt)
                price = float(order_info['price']) * 0.995
                order_sell_limit_asset_usdt = self.order_asset(symbol, 'SELL', 'LIMIT', qty, price, 'GTC')

                # 3.2.4.c
                waiting_time = 3  # 3min
                if not self.order_filled(order_sell_limit_asset_usdt, waiting_time):
                    self.reader.cancel_order(symbol, order_sell_limit_asset_usdt)
                    price = None
                    self.order_asset(symbol, 'SELL', 'MARKET', qty, price, 'FOK')
            return False
        return True

    def buy_min_asset(self, asset, qty, price):
        symbol = asset + Coins.BTC
        return self.order_asset(symbol, 'BUY', 'LIMIT', qty, price, 'FOK')

    def sell_min_asset(self, order_info, asset, result_prices):
        # 3.2.8a
        symbol = asset + Coins.USDT
        executed_qty_min = order_info['executedQty']
        min_cur_usdt_price = self.calculator.get_actual_coin_price(result_prices, asset, Coins.USDT)
        price = min_cur_usdt_price * 0.995
        order_sell_limit_min = self.order_asset(symbol, 'SELL', 'LIMIT', executed_qty_min, price, 'GTC')

        # 3.2.8b
        waiting_time = 3  # 3min
        if not self.order_filled(order_sell_limit_min, waiting_time):
            self.reader.cancel_order(symbol, order_sell_limit_min)
            price = min_cur_usdt_price * 0.99
            order_sell_limit_min = self.order_asset(symbol, 'SELL', 'LIMIT', executed_qty_min, price, 'GTC')

            # 3.2.8c
            waiting_time = 3  # 3min
            if not self.order_filled(order_sell_limit_min, waiting_time):
                self.reader.cancel_order(symbol, order_sell_limit_min)
                price = None
                self.order_asset(symbol, 'SELL', 'MARKET', executed_qty_min, price, 'FOK')

    def return_min_usdt(self, symbol, qty, price):
        # 3.2.7a
        order_sell_limit = self.order_asset(symbol, 'SELL', 'LIMIT', qty, price, 'GTC')

        # 3.2.7b
        waiting_time = 5  # 5min
        if not self.order_filled(order_sell_limit, waiting_time):
            self.reader.cancel_order(symbol, order_sell_limit)
            self.order_asset(symbol, 'SELL', 'MARKET', qty, None, 'FOK')
