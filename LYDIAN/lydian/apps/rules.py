#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

'''
Rules app handles all the operations and management of Traffic
rules. Traffic Rules shall be stored at Primary node as well as
worker nodes. Primary nodes would have all the traffic rules running
in the system at a given point of time. Rules at endpoints would only
be related to that endpoint host.
'''

import logging

from sql30 import db


from lydian.apps.base import BaseApp, exposify
from lydian.traffic.core import TrafficRule

log = logging.getLogger(__name__)


@exposify
class RulesApp(db.Model, BaseApp):
    NAME = "RULES"
    DB_NAME = 'rules.db'
    TABLE = 'rules'
    DB_SCHEMA = {
        'db_name': DB_NAME,
        'tables': [
            {
                'name': TABLE,
                'fields': TrafficRule.SCHEMA,
                'primary_key': 'ruleid'  # avoid duplicate entries.
            }]
        }
    VALIDATE_BEFORE_WRITE = True

    # Valid states
    INACTIVE = 'INACTIVE'
    ACTIVE = 'ACTIVE'

    def __init__(self, db_file=None):

        db_name = db_file or self.DB_NAME

        super(RulesApp, self).__init__(db_name=db_name)
        self._rules = {}    # represents local cache.
        self.table = self.TABLE
        self.load_from_db()

    def get(self, ruleid):
        return self._rules.get(ruleid)

    def add(self, trule, save_to_db=True):
        """
        Adds a rule in local cache and database and returns
        corresponding object.
        """
        if save_to_db:
            if trule.ruleid in self._rules:
                # Local Cache is always in sync with Database.
                self.update(condition={'ruleid': trule.ruleid},
                            **trule.as_dict())
            else:
                self.create(**trule.as_dict())
            # Commit the records.
            self.commit()
        self._rules[trule.ruleid] = trule

    def add_rules(self, trules):
        """ Adds multiple rules. """
        for trule in trules:
            self.add(trule, save_to_db=False)
        self.commit()

    def load_from_db(self):
        """ Loads rules from DB to local file."""
        records = self.read(include_header=True)
        fields = list(records[0])
        for index, rule in enumerate(records):
            if not index:
                continue  # first record is a header
            trule = TrafficRule()

            for key, val in zip(fields, list(rule)):
                setattr(trule, key, val)

            ruleid = getattr(trule, 'ruleid', None)
            if not ruleid:
                self.error("Skipped Invalid rule with no ruleid : %s",
                           trule.__dict__)
            self._rules[ruleid] = trule

    def save_to_db(self):
        """
        Save config params in local cache to database file.
        """
        curr_rule_ids = [x[0] for x in self.read()]  # first value is ruleid
        for ruleid, trule in self._rules.items():
            if ruleid in curr_rule_ids:
                self.update(condition={'ruleid': ruleid}, **trule.as_dict())
            else:
                self.create(**trule.as_dict())

        self.commit()

    def disable(self, ruleid):
        """ Disables a rule. """
        if ruleid not in self._rules:
            log.error("Invalid rule to disable : %s", ruleid)
            return

        self._rules[ruleid].state = self.INACTIVE

        where = {'ruleid': ruleid}
        self.update(condition=where, state=self.INACTIVE)
        self.commit()

    def enable(self, ruleid):
        """ Enables a rule """
        if ruleid not in self._rules:
            log.error("Invalid rule to enable : %s", ruleid)
            return

        self._rules[ruleid].state = self.ACTIVE

        where = {'ruleid': ruleid}
        self.update(condition=where, state=self.ACTIVE)
        self.commit()

    def is_enabled(self, ruleid):
        rule = self._rules.get(ruleid)

        if not rule:
            log.error("Invalid rule id : %s", ruleid)

        return rule.state == self.ACTIVE

    def close(self):
        self.save_to_db()
        super(RulesApp, self).commit()
