from src.calculator_api.calculator import Calculator
from src.reader_api.reader import Reader
from src.utils.constants import Coins
from src.utils.functions import current_milli_time, get_currencies, get_final_currencies, filter_currencies
from src import config
from src.utils.logger import get_logger, configure_logger


def order_filled_waiting(reader, calculator, symbol, order, waiting_time):
    time_delta = 0
    max_sell_time_start = current_milli_time()
    order_filled = False
    while time_delta < waiting_time:
        order_info = reader.get_order_info(symbol=symbol, orderId=order['orderId'])
        if calculator.check_order_status(order_info, 'FILLED'):
            return True
        time_delta = current_milli_time() - max_sell_time_start
    return order_filled


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
    working_amount = calculator.get_working_amount(usdt_spot_balance)
    logger.debug(f"Working amount: {working_amount}")
    max_cur = min_max_d_curs['max_d_cur'][0]
    min_cur = min_max_d_curs['min_d_cur'][0]

    # 3.2.1

    max_cur_order_price = calculator.get_actual_coin_price(result_prices, max_cur, Coins.USDT) * 1.001
    max_cur_qty = calculator.get_max_cur_qty(working_amount, max_cur_order_price)
    logger.debug(f"Buy order price for max cur: {max_cur_order_price}")
    logger.debug(f"Buy qty for max cur: {max_cur_qty}")

    # trades
    symbol = max_cur + Coins.USDT
    order_buy_limit_max = reader.create_order(symbol=symbol,
                                              side='BUY',
                                              order_type='LIMIT',
                                              quantity=max_cur_qty,
                                              price=max_cur_order_price,
                                              timeInForce='FoK'
                                              )
    order_info_limit_max = reader.get_order_info(symbol=symbol, orderId=order_buy_limit_max['orderId'])

    # 3.2.2
    if not calculator.check_order_status(order_info_limit_max, 'FILLED'):
        return

    # 3.2.3
    executed_qty_max = calculator.get_executed_qty(order_info_limit_max)

    symbol = max_cur + Coins.BTC
    order_sell_market_max = reader.create_order(symbol=symbol,
                                                side='SELL',
                                                order_type='LIMIT',
                                                quantity=executed_qty_max,
                                                price=calculator.get_actual_coin_price(result_prices, max_cur,
                                                                                       Coins.BTC),
                                                timeInForce='GTC'
                                                )

    # 3.2.4
    waiting_time = 2 * 60 * 1000  # 2min
    order_filled = order_filled_waiting(reader, calculator, symbol, order_sell_market_max, waiting_time)

    if not order_filled:
        # 3.2.4.a
        reader.cancel_order(symbol, order_sell_market_max)

        symbol = max_cur + Coins.USDT
        order_sell_limit_max_usdt = reader.create_order(symbol=symbol,
                                                        side='SELL',
                                                        order_type='LIMIT',
                                                        quantity=executed_qty_max,
                                                        price=float(order_info_limit_max['price']) * 1.0015,
                                                        timeInForce='GTC'
                                                        )
        waiting_time = 3 * 60 * 1000  # 3min
        order_filled = order_filled_waiting(reader, calculator, symbol, order_sell_limit_max_usdt, waiting_time)

        if not order_filled:
            # 3.2.4.b
            reader.cancel_order(symbol, order_sell_limit_max_usdt)

            order_sell_limit_max_usdt = reader.create_order(symbol=symbol,
                                                            side='SELL',
                                                            order_type='LIMIT',
                                                            quantity=executed_qty_max,
                                                            price=float(order_info_limit_max['price']) * 0.995,
                                                            timeInForce='GTC'
                                                            )
            order_filled = order_filled_waiting(reader, calculator, symbol, order_sell_limit_max_usdt, waiting_time)

            if not order_filled:
                # 3.2.4.c
                reader.cancel_order(symbol, order_sell_limit_max_usdt)

                reader.create_order(symbol=symbol,
                                    side='SELL',
                                    order_type='MARKET',
                                    quantity=executed_qty_max,
                                    price=None,
                                    timeInForce='FoK'
                                    )
        return

    # 3.2.5
    btc_spot_balance = reader.get_spot_balance(Coins.BTC)
    min_cur_order_price = calculator.get_actual_coin_price(result_prices, min_cur, Coins.BTC) * 1.005
    min_cur_qty = calculator.get_min_cur_qty(btc_spot_balance, min_cur_order_price)
    logger.debug(f"Buy order price for min cur: {min_cur_order_price}")
    logger.debug(f"Buy qty for min cur: {min_cur_qty}")

    symbol = min_cur + Coins.BTC
    order_buy_limit_min = reader.create_order(symbol=symbol,
                                              side='BUY',
                                              order_type='LIMIT',
                                              quantity=min_cur_qty,
                                              price=min_cur_order_price,
                                              timeInForce='FoK'
                                              )
    order_info_limit_min = reader.get_order_info(symbol=symbol, orderId=order_buy_limit_min['orderId'])

    # 3.2.6
    if calculator.check_order_status(order_info_limit_min, 'FILLED'):
        # 3.2.8a
        symbol = min_cur + Coins.USDT
        min_cur_usdt_price = calculator.get_actual_coin_price(result_prices, min_cur, Coins.USDT) * 0.995
        executed_qty_min = calculator.get_executed_qty(order_info_limit_min)
        reader.create_order(symbol=symbol,
                            side='SELL',
                            order_type='LIMIT',
                            quantity=executed_qty_min,
                            price=min_cur_usdt_price,
                            timeInForce='GTC'
                            )

    ###################################################################################################################
    else:
        # 3.2.6b
        btcusdt_order_price = reader.get_price(Coins.BTC + Coins.USDT)
        btc_qty = float(reader.get_spot_balance(Coins.BTC))

        order_sell_limit_btcusdt = reader.create_order(symbol=Coins.BTC + Coins.USDT,
                                                       side='SELL',
                                                       order_type='LIMIT',
                                                       quantity=btc_qty,
                                                       price=btcusdt_order_price * (0.0750 * 3 + 0.005),
                                                       timeInForce='GTC'
                                                       )

        # 3.2.7 sell limit order
        time_delta = 0
        btc_sell_time_start = current_milli_time()
        while (time_delta < 300000 and not calculator.check_order_status(
                reader.get_order_info(symbol=Coins.BTC + Coins.USDT,
                                      orderId=order_sell_limit_btcusdt['orderId']), 'FILLED')):
            time_delta = current_milli_time() - btc_sell_time_start

        if calculator.check_order_status(
                reader.get_order_info(symbol=Coins.BTC + Coins.USDT,
                                      orderId=order_sell_limit_btcusdt['orderId']), 'FILLED'):
            # 3.2.8 exit
            return
        # 3.2.7 new sell market order
        else:
            btc_qty = float(reader.get_spot_balance(Coins.BTC))
            reader.create_order(symbol=Coins.BTC + Coins.USDT,
                                side='SELL',
                                order_type='MARKET',
                                quantity=btc_qty,
                                price=None,
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
