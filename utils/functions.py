import time

from utils.constants import Coins


def current_milli_time():
    return round(time.time() * 1000)


def stop_robot(secs):
    time.sleep(secs)
    return


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
