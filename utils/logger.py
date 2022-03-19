import os
import logging
import datetime


def get_logger(logger_name='cryptoapis_logger'):
    return logging.getLogger(logger_name)


def configure_logger(log_dir_path=None, raw_log_level='error'):
    if log_dir_path is not None:
        os.makedirs(log_dir_path, exist_ok=True)

    log_level = raw_log_level.lower()

    if log_level == 'info':
        log_level = logging.INFO
    elif log_level == 'debug':
        log_level = logging.DEBUG
    elif log_level == 'error':
        log_level = logging.ERROR

    logger = get_logger()
    if not logger.handlers:
        __configure_logging(log_level, log_dir_path)

    return logger


def __configure_logging(log_level, path_to_log_directory):
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'

    class CustomFilter(logging.Filter):

        COLOR = {
            "DEBUG": OKBLUE,
            "INFO": OKGREEN,
            "WARNING": WARNING,
            "ERROR": FAIL,
            "CRITICAL": FAIL,
        }

        def filter(self, record):
            record.color = CustomFilter.COLOR[record.levelname]
            return True

    importer_logger = get_logger()
    importer_logger.setLevel(log_level)

    if path_to_log_directory is not None:
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
        log_filename = datetime.datetime.now().strftime('%Y-%m-%d') + '.log'
        h = logging.FileHandler(filename=os.path.join(path_to_log_directory, log_filename))
    else:
        formatter = logging.Formatter(f'%(color)s%(asctime)s : %(levelname)-8s : %(message)s\033[0m')
        importer_logger.addFilter(CustomFilter())
        h = logging.StreamHandler()

    h.setLevel(log_level)
    h.setFormatter(formatter)
    importer_logger.addHandler(h)
