import time
import numpy as np

from src.calculator_api.checker import Checker
from src.utils.constants import Coins


def current_milli_time():
    return round(time.time() * 1000)


def get_currencies():
    return [Coins.CKB,
            Coins.DGB,
            Coins.ZIL,
            Coins.TRX,
            Coins.VET,
            Coins.RVN,
            Coins.IOTX,
            Coins.CTXC,
            Coins.SYS,
            Coins.NULS,
            Coins.DUSK,
            Coins.FLUX,
            Coins.PYR,
            Coins.MC,
            Coins.REQ,
            Coins.GXS,
            Coins.ANT,
            Coins.LTO,
            Coins.WAN]


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
