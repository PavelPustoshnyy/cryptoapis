import time
import numpy as np
import pandas as pd

from src.calculator_api.checker import Checker
from src.utils.constants import Coins


def current_milli_time():
    return round(time.time() * 1000)


def get_currencies(reader, calculator):
    listing = reader.get_listing()
    intersection = calculator.get_btusdt_pairs(listing)
    all_tickers = reader.get_tickers()

    btcusdt_price = calculator.get_price(all_tickers, Coins.BTC + Coins.USDT)

    symbols = []
    for symbol in intersection:
        klines_btc = pd.DataFrame(reader.get_historical_klines(symbol + Coins.BTC))
        klines_usdt = pd.DataFrame(reader.get_historical_klines(symbol + Coins.USDT))
        if not (klines_btc.empty or klines_usdt.empty):
            klines_btc['usdt_vol'] = klines_btc[7].apply(float) * btcusdt_price
            klines_usdt['usdt_vol'] = klines_usdt[7].apply(float)

            relation_btc = klines_btc[klines_btc['usdt_vol'] > 5].size / klines_btc.size
            relation_usdt = klines_usdt[klines_usdt['usdt_vol'] > 5].size / klines_usdt.size

            if relation_btc > 0.85 and relation_usdt > 0.85:
                symbols.append(symbol)
    return symbols


def get_final_currencies(crns, stp_lst):
    return [x for x in crns if x not in stp_lst]


def filter_currencies(logger, rdr, clc, crns):
    stp_lst = list()
    checker = Checker(logger)
    for crn in crns:
        btc_trades = rdr.get_trades(crn, Coins.BTC)
        q_sum = clc.get_q_sum(btc_trades)
        logger.debug(f"{crn}BTC V (sum(q)): {q_sum}")
        if checker.check_sum(stp_lst, q_sum, crn):
            usdt_trades = rdr.get_trades(crn, Coins.USDT)
            q_sum = clc.get_q_sum(usdt_trades)
            checker.check_sum(stp_lst, q_sum, crn)
            logger.debug(f"{crn}USDT V (sum(q)): {q_sum}")
    return stp_lst


def dec_len(price):
    dec = np.format_float_positional(float(price), trim='-')
    if len(str(dec).split('.')) < 2:
        return 0
    return len(str(dec).split('.')[1])


def truncate_round(value, length):
    dec = np.format_float_positional(float(value), trim='-')
    if dec_len(value) <= length:
        return float(dec)
    else:
        return float(str(dec).split('.')[0] + '.' + str(dec).split('.')[1][:length])
