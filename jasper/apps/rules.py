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


from axon.apps.base import BaseApp

log = logging.getLogger(__name__)


class TrafficRule(object):
    pass


class RulesApp(db.Model, BaseApp):
    NAME = "RULES"
    DB_NAME = 'rules.db'
    TABLE = 'rules'
    DB_SCHEMA = {
        'db_name': DB_NAME,
        'tables': [
            {
                'name': TABLE,
                'fields': {
                    'ruleid': 'text',       # Unique id of rule.

                    'src': 'text',          # source endpoint
                    'dst': 'text',          # destination endpoint
                    'protocol': 'text',     # Protocol : TCP/UDP/HTTP
                    'port': 'text',         # port
                    'connected': 'text',    # Ping to PASS or FAIL

                    'payload': 'text',      # Payload for rule.
                    'packet': 'text',       # Packet size for traffic.
                    'tries': 'text',        # Number of tries.

                    'src_host': 'text',     # Source host Management IP
                    'dst_host': 'text',     # Destination host Management IP

                    'purpose':  'text',     # context : CLIENT/SERVER/PERSIST
                    'username': 'text',     # run traffic as. 'root' by default
                    'target': 'text',       # Host / Namespace / Container

                    'state': 'text',        # ENABLED/DISABLED
                    },
                'primary_key': 'ruleid'  # avoid duplicate entries.
            }]
        }
    VALIDATE_BEFORE_WRITE = True

    # Valid states
    INACTIVE = 'INACTIVE'
    ACTIVE = 'ACTIVE'

    def __init__(self, traffic_manager, db_file=None):

        db_name = db_file or self.DB_NAME

        super(RulesApp, self).__init__(db_name=db_name)
        self._rules = {}    # represents local cache.
        self._traffic_manager = traffic_manager
        self.table = self.TABLE

    def disable(self, ruleid):
        """ Disables a rule. """
        if ruleid not in self._rules:
            log.error("Invalid rule to disable : %s", ruleid)
            return
        self._traffic_manager.stop(ruleid)

        self._rules[ruleid].state = self.INACTIVE

        where = {'ruleid': ruleid}
        self.update(condition=where, state=self.INACTIVE)
        self.commit()

    def enable(self, ruleid):
        """ Enables a rule """
        if ruleid not in self._rules:
            log.error("Invalid rule to enable : %s", ruleid)
            return
        self._traffic_manager.start(ruleid)

        self._rules[ruleid].state = self.ACTIVE

        where = {'ruleid': ruleid}
        self.update(condition=where, state=self.ACTIVE)
        self.commit()

    def add(self, rule, save_to_db=True):
        """ Adds a rule in local cache and database. """
        ruleid = rule['ruleid']
        if ruleid in self._rules:
            log.error("Rule wih id %s already exists", ruleid)
            return
        trule = TrafficRule()

        for key, val in rule.items():
            setattr(trule, key, val)

        if 'state' not in rule:
            trule.state = rule.get('state', self.ACTIVE)
            # create a local copy instead of modifying
            # the input parameter.
            _rule = {k: v for k, v in rule.items()}
            _rule['state'] = self.ACTIVE
        else:
            _rule = rule

        self._rules[ruleid] = trule
        self.create(**_rule)
        if save_to_db:
            self.commit()

    def add_rules(self, rules):
        """ Adds multiple rules. """
        for rule in rules:
            self.add(rule, save_to_db=False)
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
                self.update(condition={'ruleid': ruleid}, **trule.__dict__)
            else:
                self.create(**trule.__dict__)

        self.commit()

    def get(self, ruleid):
        return self._rules.get(ruleid, None)

    def is_enabled(self, ruleid):
        rule = self._rules.get(ruleid, None)

        if not rule:
            log.error("Invalid rule id : %s", ruleid)

        return rule.state == self.ACTIVE
