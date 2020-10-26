#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import os
import setuptools

# In python < 2.7.4, a lazy loading of package `pbr` will break
# setuptools if some other modules registered functions in `atexit`.
# solution from: http://bugs.python.org/issue15881#msg170215
try:
    import multiprocessing  # noqa
except ImportError:
    pass


console_mapper = {
    'posix': 'axon_service = axon.controller.rpyc_controller:main',
    'nt': 'axon_service = axon.controller.windows.axon_service:main'
}


setuptools.setup(
    setup_requires=['pbr>=2.0.0'],
    entry_points={
        'console_scripts': [console_mapper[os.name]]
    },
    pbr=True)
