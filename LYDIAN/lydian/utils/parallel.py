#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging

from concurrent.futures import ThreadPoolExecutor, as_completed

from lydian.apps.config import get_param

log = logging.getLogger(__name__)

THREAD_COUNT = get_param('DEFAULT_CONCURRENCY', 32)


def ThreadPool(func, params, timeout=None, blocking=True, workers=None):
    results = {}
    max_workers = workers or THREAD_COUNT

    with ThreadPoolExecutor(max_workers=max_workers) as tpool:
        futures = {}
        for _ident, _args, _kwargs in params:
            _tfunc = tpool.submit(func, *_args, **_kwargs)
            futures[_tfunc] = _ident

        if not blocking:
            return None

        for future in as_completed(futures):
            ident = futures[future]
            try:
                results[ident] = future.result()
            except Exception as err:
                log.warn("Error for %s - %s", ident, err)
    return results
