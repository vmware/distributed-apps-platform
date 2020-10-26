#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

'''
Base class for all Apps on the platform.
'''

class BaseApp(object):

    NAME = ''

    @property
    def name(self):
        """
        Returns name of the App.
        """
        assert self.NAME, "Invalid Name for app"
        return self.NAME

