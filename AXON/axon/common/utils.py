import logging
import os

from axon.common import consts


def create_log_dir(log_dir):
    """
    Create Log directory
    """
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    except Exception as e:
        # TODO Change the exception type
        raise RuntimeError(
            "Failed to create log directory %s due to %s" % (log_dir, e))


def setup_logging(log_dir=None, log_file=None):
    """
    Sets up Logging handlers and other environment.
    """
    log_dir = log_dir if log_dir else consts.LOG_DIR
    log_file = log_file if log_file else consts.LOG_FILE
    create_log_dir(log_dir)

    log_file_name = os.path.join(log_dir, log_file)
    log_formatter = logging.Formatter(
        '%(asctime)s::%(levelname)s::%(threadName)s::'
        '%(module)s[%(lineno)04s]::%(message)s')
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    root_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file_name)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    return root_logger
