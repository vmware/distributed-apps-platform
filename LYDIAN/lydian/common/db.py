#!/usr/bin/env python
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from sql30 import db

from lydian.apps import config


class LydianDB(db.Model):

    def __init__(self, *args, **kwargs):
        db_loc = config.get_param("LYDIAN_DB_DIR", "./")
        kwargs['db_loc'] = kwargs.get('db_loc', db_loc)
        super(LydianDB, self).__init__(*args, **kwargs)
