from calculator_api.calculator import Calculator
from reader_api.reader import Reader
from utils.constants import Coins
from utils.functions import current_milli_time, get_currencies, get_final_currencies
import config
from utils.logger import get_logger, configure_logger


def filter_currencies(rdr, clc, crns):
    stp_lst = list()
    for crn in crns:
        btc_trades = rdr.get_trades(crn, Coins.BTC)
        q_sum = clc.get_q_sum(btc_trades)
        logger.debug(f"{crn}BTC V (sum(q)): {q_sum}")
        if clc.check_sum(stp_lst, q_sum, crn):
            usdt_trades = rdr.get_trades(crn, Coins.USDT)
            q_sum = clc.get_q_sum(usdt_trades)
            clc.check_sum(stp_lst, q_sum, crn)
            logger.debug(f"{crn}USDT V (sum(q)): {q_sum}")
    return stp_lst


def main():
    logger.info("New cycle started")
    beginning_time = current_milli_time()
    reader = Reader(logger)
    calculator = Calculator(logger)

    trades_df = reader.get_trades(Coins.BTC, Coins.USDT)
    price_change = calculator.get_price_change(trades_df)
    logger.debug(f"BTCUSDT price change: {price_change}")

    if calculator.check_limits(price_change) or config.DEBUG:
        currencies = get_currencies()

        stop_list = filter_currencies(reader, calculator, currencies)

        final_currencies = get_final_currencies(currencies, stop_list)
        logger.info(f"Final currencies which not in stop list: {final_currencies}")

        all_tickers = reader.get_tickers()
        d_curs, old_result_prices = calculator.get_d_curs_and_result_prices(all_tickers, final_currencies)
        logger.debug(f"Old result prices: {old_result_prices}")
        logger.debug(f"d(curs): {d_curs}")

        min_max_d_curs = calculator.get_min_max(d_curs)
        logger.debug(f"Min and max d(cur): {min_max_d_curs}")

        if calculator.check_min_max_d_cur(min_max_d_curs):
            spot_balance = reader.get_spot_balance(Coins.USDT)
            if config.DEBUG:
                spot_balance = reader.get_spot_balance(Coins.BTC)
            logger.debug(f"Spot balance in USDT (when DEBUG=TRUE in BTC): {spot_balance}")

            working_amount = calculator.get_working_amount(spot_balance)
            logger.debug(f"Working amount: {working_amount}")

            new_all_tickers = reader.get_tickers()
            min_and_max_curs = [min_max_d_curs['max_d_cur'][0], min_max_d_curs['min_d_cur'][0], Coins.BTC]
            fresh_d_curs, fresh_result_prices = calculator.get_d_curs_and_result_prices(new_all_tickers,
                                                                                        min_and_max_curs)
            logger.debug(f"Fresh result prices: {fresh_result_prices}")

            max_cur_order_price = calculator.get_max_cur_order_price(min_max_d_curs, fresh_result_prices)
            max_cur_qty = calculator.get_max_cur_qty(working_amount, max_cur_order_price)
            logger.debug(f"Buy order price for max cur: {max_cur_order_price}")
            logger.debug(f"Buy qty for max cur: {max_cur_qty}")

            btc_spot_balance = reader.get_spot_balance(Coins.BTC)
            min_cur_order_price = calculator.get_min_cur_order_price(min_max_d_curs, fresh_result_prices)
            min_cur_qty = calculator.get_min_cur_qty(btc_spot_balance, min_cur_order_price)
            logger.debug(f"Buy order price for min cur: {min_cur_order_price}")
            logger.debug(f"Buy qty for min cur: {min_cur_qty}")

    ending_time = current_milli_time()
    duration_of_cycle = ending_time - beginning_time
    logger.debug(f"Duration of cycle: {duration_of_cycle}ms")


if __name__ == '__main__':
    configure_logger(log_dir_path=config.LOG_DIR_PATH, raw_log_level=config.RAW_LOG_LEVEL)
    logger = get_logger()
    logger.info("Program started")
    while True:
        main()
