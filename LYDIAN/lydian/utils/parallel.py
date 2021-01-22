#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging

from concurrent.futures import ThreadPoolExecutor, as_completed

from lydian.apps.config import get_param

log = logging.getLogger(__name__)

THREAD_COUNT = get_param('DEFAULT_CONCURRENCY', 32)


def ThreadPool(func, args, timeout=None, blocking=True):
    results = {}
    workers = THREAD_COUNT

    with ThreadPoolExecutor(max_workers=workers) as tpool:
        futures = {}
        for arg in args:
            _tfunc = tpool.submit(func, *arg)
            futures[_tfunc] = arg

        if not blocking:
            return None

        for future in as_completed(futures):
            ident = futures[future]
            try:
                results[ident] = future.result()
            except Exception as err:
                log.warn("Error for %s - %s", ident, err)
    return results
