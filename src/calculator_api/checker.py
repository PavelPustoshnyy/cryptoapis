import time

from src import config


def stop_robot(secs):
    time.sleep(secs)
    return


class Checker:
    def __init__(self, logger):
        self.logger = logger

    @staticmethod
    def check_order_status(order_info, status):
        return order_info['status'] == status

    def check_sum(self, stop_list, q_sum, currency):
        if q_sum <= config.Q_LIMIT:
            self.logger.debug(f"{currency} has been added to the stop list.")
            stop_list.append(currency)
            return False
        return True

    def check_limits(self, price_change):
        if config.MIN_LIMIT < price_change <= config.MAX_LIMIT:
            self.logger.info(f"Price change per minute is {price_change}. Stopping the robot for a short time.")
            self.logger.info("stopped_4_min: True")
            if config.DEBUG:
                return True
            stop_robot(config.SHORT_STOP)
            return False

    def check_limits(self, price_change):
        if config.MIN_LIMIT < price_change <= config.MAX_LIMIT:
            self.logger.info(f"Price change per minute is {price_change}. Stopping the robot for a short time.")
            self.logger.info("stopped_4_min: True")
            if config.DEBUG:
                return True
            stop_robot(config.SHORT_STOP)
            return False

        elif config.MAX_LIMIT < price_change:
            self.logger.info(f"Price change per minute is {price_change}. Stopping the robot for a long time.")
            self.logger.info("stopped_3_days(boolean): True")
            if config.DEBUG:
                return True
            stop_robot(config.LONG_STOP)
            return False

        else:
            self.logger.info(f"Price change per minute is {price_change}. Continuation of the robot work.")
            self.logger.info("stopped_4_min: False")
            self.logger.info("stopped_3_days: False")
            return True

    def check_min_max_d_cur(self, min_max_d_curs):
        dx = (min_max_d_curs['max_d_cur'][1] - min_max_d_curs['min_d_cur'][1]) / min_max_d_curs['min_d_cur'][1] * 100
        self.logger.debug(f"(max - min) / min = {dx}")
        self.logger.debug(f"(max - min) / min > MIN_MAX_D_CUR: {dx > config.MIN_MAX_D_CUR}")
        return dx > config.MIN_MAX_D_CUR
