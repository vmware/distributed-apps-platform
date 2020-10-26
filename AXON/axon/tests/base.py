#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os

import fixtures
import testtools

LOG = logging.getLogger(__name__)


_TRUE_VALUES = ('True', 'true', '1', 'yes')
_FALSE_VALUES = ('False', 'false', '0', 'no')
_BASE_LOG_LEVELS = ('DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL')
_LOG_LEVELS = dict((n, getattr(logging, n)) for n in _BASE_LOG_LEVELS)
_LOG_LEVELS.update({
    'TRACE': 5,
})
_LOG_FORMAT = "%(levelname)8s [%(name)s] %(message)s"


def _try_int(value):
    """Try to make some value into an int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class ConfigureLogging(fixtures.Fixture):

    DEFAULT_FORMAT = _LOG_FORMAT

    def __init__(self, format=DEFAULT_FORMAT):
        super(ConfigureLogging, self).__init__()
        self._format = format
        self.level = None
        _os_debug = os.environ.get('OS_DEBUG')
        _os_level = _try_int(_os_debug)
        if _os_debug in _TRUE_VALUES:
            self.level = logging.DEBUG
        elif _os_level is not None:
            self.level = _os_level
        elif _os_debug in _LOG_LEVELS:
            self.level = _LOG_LEVELS[_os_debug]
        elif _os_debug and _os_debug not in _FALSE_VALUES:
            raise ValueError('OS_DEBUG=%s is invalid.' % (_os_debug))
        self.capture_logs = os.environ.get('OS_LOG_CAPTURE') in _TRUE_VALUES
        self.logger = None

    def setUp(self):
        super(ConfigureLogging, self).setUp()
        if self.capture_logs:
            self.logger = self.useFixture(
                fixtures.FakeLogger(
                    format=self._format,
                    level=self.level,
                    nuke_handlers=True,
                )
            )
        else:
            logging.basicConfig(format=self._format, level=self.level)


class CaptureOutput(fixtures.Fixture):

    def __init__(self, do_stdout=None, do_stderr=None):
        super(CaptureOutput, self).__init__()
        if do_stdout is None:
            self.do_stdout = (os.environ.get('OS_STDOUT_CAPTURE')
                              in _TRUE_VALUES)
        else:
            self.do_stdout = do_stdout
        if do_stderr is None:
            self.do_stderr = (os.environ.get('OS_STDERR_CAPTURE')
                              in _TRUE_VALUES)
        else:
            self.do_stderr = do_stderr
        self.stdout = None
        self.stderr = None

    def setUp(self):
        super(CaptureOutput, self).setUp()
        if self.do_stdout:
            self._stdout_fixture = fixtures.StringStream('stdout')
            self.stdout = self.useFixture(self._stdout_fixture).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', self.stdout))
        if self.do_stderr:
            self._stderr_fixture = fixtures.StringStream('stderr')
            self.stderr = self.useFixture(self._stderr_fixture).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', self.stderr))


class BaseTestCase(testtools.TestCase):

    def __init__(self, *args, **kwds):
        super(BaseTestCase, self).__init__(*args, **kwds)

    def addCleanup(self, function, *args, **kwargs):
        super(BaseTestCase, self).addCleanup(function, *args, **kwargs)

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self._fake_output()
        self._fake_logs()

    def _fake_output(self):
        self.output_fixture = self.useFixture(CaptureOutput())

    def _fake_logs(self):
        self.log_fixture = self.useFixture(ConfigureLogging())
