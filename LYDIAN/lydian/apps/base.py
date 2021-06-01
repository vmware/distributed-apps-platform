#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

'''
Base class for all Apps on the platform.
'''

import collections

class BaseApp(object):

    NAME = ''

    @property
    def name(self):
        """
        Returns name of the App.
        """
        assert self.NAME, "Invalid Name for app"
        return self.NAME


def exposify(cls):
    for key in dir(cls):
        val = getattr(cls, key)
        if isinstance(val, collections.Callable) and not key.startswith("_"):
            setattr(cls, "exposed_%s" % (key,), val)
    return cls