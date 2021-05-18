# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

PYTHONPATH=/lydian/lydian.egg
export PYTHONPATH

python -mlydian.controller.rpyc_controller &
