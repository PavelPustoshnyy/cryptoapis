from src.calculator_api.calculator import Calculator
from src.calculator_api.trader import Trader
from src.reader_api.reader import Reader
from src.utils.constants import Coins
from src.utils.functions import current_milli_time, get_currencies, get_final_currencies, filter_currencies
from src import config
from src.utils.logger import get_logger, configure_logger


def main():
    logger.info("New cycle started")
    beginning_time = current_milli_time()
    reader = Reader(logger)
    calculator = Calculator(logger)
    trader = Trader(logger, reader, calculator)

    trades_df = reader.get_trades(Coins.BTC, Coins.USDT)
    price_change = calculator.get_price_change(trades_df)
    logger.debug(f"BTCUSDT price change: {price_change}")

    if not (calculator.check_limits(price_change) or config.DEBUG):
        return
    currencies = get_currencies()

    stop_list = filter_currencies(logger, reader, calculator, currencies)

    final_currencies = get_final_currencies(currencies, stop_list)
    logger.info(f"Final currencies which not in stop list: {final_currencies}")

    all_tickers = reader.get_tickers()
    d_curs, result_prices = calculator.get_d_curs_and_result_prices(all_tickers, final_currencies)
    logger.debug(f"Old result prices: {result_prices}")
    logger.debug(f"d(curs): {d_curs}")

    min_max_d_curs = calculator.get_min_max(d_curs)
    logger.debug(f"Min and max d(cur): {min_max_d_curs}")

    if not (calculator.check_min_max_d_cur(min_max_d_curs)):
        return

    # 3rd block
    # 3.1
    usdt_spot_balance = reader.get_spot_balance(Coins.USDT)
    logger.debug(f"Spot balance in USDT (when DEBUG=TRUE in BTC): {usdt_spot_balance}")
    working_amount = float(usdt_spot_balance) * 0.10
    logger.debug(f"Working amount: {working_amount}")
    max_cur = min_max_d_curs['max_d_cur'][0]
    min_cur = min_max_d_curs['min_d_cur'][0]

    # 3.2.1
    buy_max_asset_price = calculator.get_actual_coin_price(result_prices, max_cur, Coins.USDT) * 1.001
    max_cur_qty = working_amount / buy_max_asset_price
    logger.debug(f"Buy order price for max cur: {buy_max_asset_price}")
    logger.debug(f"Buy qty for max cur: {max_cur_qty}")

    # trades
    order_buy_info_limit_max = trader.buy_max_asset(max_cur, max_cur_qty, buy_max_asset_price)

    # 3.2.2
    if not calculator.check_order_status(order_buy_info_limit_max, 'FILLED'):
        return

    # 3.2.3
    executed_qty_max = order_buy_info_limit_max['executedQty']
    sell_max_asset_price = calculator.get_actual_coin_price(result_prices, max_cur, Coins.BTC)
    order_sell_info_limit_max = trader.sell_max_asset(max_cur, executed_qty_max, sell_max_asset_price)

    # 3.2.4
    if not trader.return_max_usdt(order_sell_info_limit_max, max_cur):
        return

    # 3.2.5
    btc_spot_balance = reader.get_spot_balance(Coins.BTC)
    min_cur_order_price = calculator.get_actual_coin_price(result_prices, min_cur, Coins.BTC) * 1.005
    min_cur_qty = calculator.get_min_cur_qty(btc_spot_balance, min_cur_order_price)
    logger.debug(f"Buy order price for min cur: {min_cur_order_price}")
    logger.debug(f"Buy qty for min cur: {min_cur_qty}")

    order_buy_info_limit_min = trader.buy_min_asset(min_cur, min_cur_qty, min_cur_order_price)

    # 3.2.6
    if calculator.check_order_status(order_buy_info_limit_min, 'FILLED'):
        # 3.2.8
        trader.sell_min_asset(order_buy_info_limit_min, min_cur, result_prices)
        return

    # 3.2.7
    symbol = Coins.BTC + Coins.USDT
    btc_qty = float(reader.get_spot_balance(Coins.BTC))
    btcusdt_price = float(order_buy_info_limit_max['price']) / float(order_sell_info_limit_max['price'])
    trader.return_min_usdt(symbol, btc_qty, btcusdt_price)

    # 3.2.7c
    ending_time = current_milli_time()
    duration_of_cycle = ending_time - beginning_time
    logger.debug(f"Duration of cycle: {duration_of_cycle}ms")
    return


if __name__ == '__main__':
    configure_logger(log_dir_path=config.LOG_DIR_PATH, raw_log_level=config.RAW_LOG_LEVEL)
    logger = get_logger()
    logger.info("Program started")
    while True:
        main()
