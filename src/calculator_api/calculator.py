import copy

from src.utils.constants import Params, Coins
import pandas as pd


class Calculator:
    def __init__(self, logger):
        self.logger = logger

    def get_price_change(self, trades_df):
        p_start = trades_df.iloc[0]['p']
        p_end = trades_df.iloc[-1]['p']
        self.logger.info(f"BTCUSDT price: {p_end}")
        price_change = abs((p_end - p_start) / p_start * 100)
        return price_change

    @staticmethod
    def get_q_sum(btc_trades):
        if btc_trades.empty:
            q_sum = 0
        else:
            q_sum = btc_trades.q.sum()
        return q_sum

    @staticmethod
    def get_all_coin_prices(tickers, fnl_crns):
        all_coin_prices = dict()
        for currency in fnl_crns:
            coins = [f'{currency}{Coins.BTC}', f'{currency}{Coins.USDT}']
            for t in tickers:
                if t[Params.SYMBOL] in coins:
                    all_coin_prices[t[Params.SYMBOL]] = float(t['price'])
        return all_coin_prices

    @staticmethod
    def create_blank_price_dict(fnl_crns):
        blank_price_dict = dict()
        for crn in fnl_crns:
            blank_price_dict[crn] = {Coins.BTC: 0, Coins.USDT: 0}
        return blank_price_dict

    @staticmethod
    def fill_blank_price_dict(all_coin_prices, blank_price_dict):
        price_dict = copy.deepcopy(blank_price_dict)
        for coin in all_coin_prices:
            if coin[-3:] == Coins.BTC:
                price_dict[coin[:-3]][Coins.BTC] = all_coin_prices[coin]
            else:
                price_dict[coin[:-4]][Coins.USDT] = all_coin_prices[coin]
        return price_dict

    @staticmethod
    def get_result_prices(all_coin_prices, price_dict):
        result_prices = copy.deepcopy(price_dict)
        for cur in all_coin_prices:
            if cur[-3:] == Coins.BTC:
                result_prices[cur[:-3]][Coins.BTC] = all_coin_prices[cur]
            else:
                result_prices[cur[:-4]][Coins.USDT] = all_coin_prices[cur]
        return result_prices

    def get_d_curs_and_result_prices(self, tickers, fnl_crns):
        all_coin_prices = self.get_all_coin_prices(tickers, fnl_crns)
        blank_price_dict = self.create_blank_price_dict(fnl_crns)
        price_dict = self.fill_blank_price_dict(all_coin_prices, blank_price_dict)
        result_prices = self.get_result_prices(all_coin_prices, price_dict)

        d_curs = dict()
        for cur in result_prices:
            d_curs[cur] = (1. / result_prices[cur][Coins.USDT]) * result_prices[cur][Coins.BTC]
        return d_curs, result_prices

    @staticmethod
    def get_min_max(d_curs):
        max_symbol = max(d_curs, key=d_curs.get)
        min_symbol = min(d_curs, key=d_curs.get)
        min_max = {'max_d_cur': (max_symbol, d_curs[max_symbol]),
                   'min_d_cur': (min_symbol, d_curs[min_symbol]), }
        return min_max

    @staticmethod
    def get_min_cur_qty(btc_spot_balance, min_cur_order_price):
        return float(btc_spot_balance) / min_cur_order_price

    @staticmethod
    def get_actual_coin_price(prices, coin, cur):
        return float(prices[coin][cur])

    @staticmethod
    def get_btusdt_pairs(listing):
        btc_set = set()
        usdt_set = set()
        for symbol in listing:
            if symbol.endswith(Coins.BTC):
                btc_set.add(symbol[:-len(Coins.BTC)])
            elif symbol.endswith(Coins.USDT):
                usdt_set.add(symbol[:-len(Coins.USDT)])

        return btc_set.intersection(usdt_set)

    @staticmethod
    def get_price(all_tickers, symbol):
        all_tickers = pd.DataFrame(all_tickers)
        return float(all_tickers.loc[all_tickers['symbol'] == symbol]['price'].values[0])
