#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os

from lydian.apps import config

LOG_DIR = config.get_param('LYDIAN_LOG_DIR')
LOG_FILE = config.get_param('LYDIAN_LOG_FILE')


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


def set_external_log_level():
    """
    Sets logging level of external modules.
    """
    levels = {
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'ERROR': logging.ERROR,
    }
    paramiko_logger = logging.getLogger('paramiko')
    # NOTE : paramiko 'INFO' level is too verbose.
    log_level = config.get_param('PARAMIKO_LOG_LEVEL', 'ERROR')
    log_level = log_level.upper()
    paramiko_logger.setLevel(levels[log_level])

    rpyc_logger = logging.getLogger('rpyc')
    log_level = config.get_param('RPYC_LOG_LEVEL', 'INFO')
    log_level = log_level.upper()
    rpyc_logger.setLevel(levels[log_level])


def setup_logging(log_dir=None, log_file=None):
    """
    Sets up Logging handlers and other environment.
    """
    log_dir = log_dir or LOG_DIR
    log_file = log_file or LOG_FILE

    create_log_dir(log_dir)

    log_file_name = os.path.join(log_dir, log_file)
    log_formatter = logging.Formatter(
        '%(asctime)s::%(levelname)s::%(threadName)s::'
        '%(module)s[%(lineno)04s]::%(message)s')
    root_logger = logging.getLogger()
    # if root_logger.handlers:
    #    return
    root_logger.setLevel(logging.INFO)
    set_external_log_level()
    file_handler = logging.FileHandler(log_file_name, mode='w')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    return root_logger
