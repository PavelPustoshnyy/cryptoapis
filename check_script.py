from src.reader_api.reader import Reader
from src.utils.logger import get_logger

logger = get_logger()
symbol = 'BTCUSDT'
logger.info("Check script started")
reader = Reader(logger)
trades = reader.get_my_trades(symbol)
print("trades: ", trades)
print("order: ", reader.get_order_info(symbol, trades[0]["orderId"]))
order_info = reader.get_order_info(symbol='BTCUSDT',
                                               orderId=trades[0]["orderId"])
print(order_info)

print(reader.get_price("BTCUSDT"))
