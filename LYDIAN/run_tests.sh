#!/bin/sh
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
python -m unittest discover -p test_background.py lydian/tests/common
python -m unittest discover -p test_mocktraffic.py lydian/tests/integration
