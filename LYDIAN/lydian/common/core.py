#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import lydian.apps.config as conf

class Subscribe(object):

    CONFIG_PARAMS = []

    def __init__(self):
        self._config_params = {}
        for param in self.CONFIG_PARAMS:
            self._config_params[param] = conf.get_param(param)

        # Subscribe to the updates of following PARAM(s)
        conf.get_configs().subscribe_notification(
            params=self.CONFIG_PARAMS,
            subscriber=self,
            callback='update_config'
        )

    def update_config(self, param):
        self._config_params[param] = conf.get_param(param)

    def get_config(self, param):
        return self._config_params[param]

    def set_config(self, param, val):
        self._config_params[param] = val
