from calculator_api.calculator import Calculator
from reader_api.reader import Reader
from utils.constants import Coins
from utils.functions import current_milli_time, get_currencies, get_final_currencies, filter_currencies
import config
from utils.logger import get_logger, configure_logger


def main():
    logger.info("New cycle started")
    beginning_time = current_milli_time()
    reader = Reader(logger)
    calculator = Calculator(logger)

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
    d_curs, old_result_prices = calculator.get_d_curs_and_result_prices(all_tickers, final_currencies)
    logger.debug(f"Old result prices: {old_result_prices}")
    logger.debug(f"d(curs): {d_curs}")

    min_max_d_curs = calculator.get_min_max(d_curs)
    logger.debug(f"Min and max d(cur): {min_max_d_curs}")

    if not (calculator.check_min_max_d_cur(min_max_d_curs)):
        return
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

    order_buy_limit_max = reader.create_order(symbol=min_max_d_curs['max_d_cur'][0] + Coins.USDT,
                                              side='BUY',
                                              order_type='LIMIT',
                                              quantity=max_cur_qty,
                                              price=max_cur_order_price,
                                              timeInForce='FoK'
                                              )
    order_info = reader.get_order_info(symbol=min_max_d_curs['max_d_cur'][0] + Coins.USDT,
                                       orderId=order_buy_limit_max['orderId'])
    if not calculator.check_order_status(order_info, 'FILLED'):
        return

    executed_qty_max = calculator.get_executed_qty(order_info)
    reader.create_order(symbol=min_max_d_curs['max_d_cur'][0] + Coins.BTC,
                        side='SELL',
                        order_type='MARKET',
                        quantity=executed_qty_max,
                        price=None,
                        timeInForce='FoK'
                        )

    btc_spot_balance = reader.get_spot_balance(Coins.BTC)
    min_cur_order_price = calculator.get_min_cur_order_price(min_max_d_curs, fresh_result_prices)
    min_cur_qty = calculator.get_min_cur_qty(btc_spot_balance, min_cur_order_price)
    logger.debug(f"Buy order price for min cur: {min_cur_order_price}")
    logger.debug(f"Buy qty for min cur: {min_cur_qty}")

    order_buy_limit_min = reader.create_order(symbol=min_max_d_curs['min_d_cur'][0] + Coins.BTC,
                                              side='BUY',
                                              order_type='LIMIT',
                                              quantity=min_cur_qty,
                                              price=min_cur_order_price,
                                              timeInForce='FoK'
                                              )
    order_info = reader.get_order_info(symbol=min_max_d_curs['min_d_cur'][0] + Coins.BTC,
                                       orderId=order_buy_limit_min['orderId'])
    if calculator.check_order_status(order_info, 'FILLED'):
        executed_qty_min = calculator.get_executed_qty(order_info)
        reader.create_order(symbol=min_max_d_curs['min_d_cur'][0] + Coins.USDT,
                            side='SELL',
                            order_type='MARKET',
                            quantity=executed_qty_min,
                            price=None,
                            timeInForce='FoK'
                            )
    else:
        order_sell_limit_btcusdt = reader.create_order(symbol=Coins.BTC + Coins.USDT,
                                                       side='SELL',
                                                       order_type='LIMIT',
                                                       quantity=,  # TODO
                                                       price=min_cur_order_price * (0.0750 * 3 + 0.005),  # TODO
                                                       timeInForce='GTC'
                                                       )

        time_delta = 0
        btc_sell_time_start = current_milli_time()
        while (time_delta < 300000 and not calculator.check_order_status(
                reader.get_order_info(symbol=Coins.BTC + Coins.USDT,
                                      orderId=order_sell_limit_btcusdt['orderId']), 'FILLED')):
            time_delta = current_milli_time() - btc_sell_time_start

        if calculator.check_order_status(
                reader.get_order_info(symbol=Coins.BTC + Coins.USDT,
                                      orderId=order_sell_limit_btcusdt['orderId']), 'FILLED'):
            return
        else:
            reader.create_order(symbol=Coins.BTC + Coins.USDT,
                                side='SELL',
                                order_type='MARKET',
                                quantity=,  # TODO
                                price=min_cur_order_price * (0.0750 * 3 + 0.005),  # TODO
                                timeInForce='FoK'
                                )

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
