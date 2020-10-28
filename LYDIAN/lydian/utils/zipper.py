#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import importlib
import logging
import os
import zipfile

'''
A simple module for zipping files and creating egg files.
'''


class Zipper(object):
    EXPAND_LINKS = True
    SKIP_COMPILED = True

    def __init__(self, output_file, source=None):
        # Output file with path
        self.dst = output_file

        # input source for zipping
        self.src = source

        self.modules = []

        # skip compiled code
        self.skip_compiled = self.SKIP_COMPILED

        self.clear()

    def clear(self):
        # overwrite existing egg if any.
        with zipfile.ZipFile(self.dst, "w") as zf:
            _ = zf

    def add_module(self, module_name):
        # Import modules like 'pika', 'rpyc'
        # Basically takes care of knowing what all to zip
        try:
            if module_name in self.modules:
                # TODO : message already imported.
                return
            mod = importlib.import_module(module_name)
            modpath, _ = os.path.split(mod.__file__)

            # pack the modules at root level. it makes importing
            # modules from egg directly without modifying PYTHONPATH
            self._write(srcdir=modpath, append=True, atroot=module_name)
        except Exception as err:
            # TODO : Fix the error
            _ = err
            pass

    def add_file(self, filename, arcname=None):
        if not os.path.isfile(filename):
            return
        with zipfile.ZipFile(self.dst, "a") as zf:
            arcname = filename if not arcname else arcname
            zf.write(filename=filename, arcname=arcname)

    def add_dir(self, dirname, atroot=None):
        self._write(srcdir=dirname, append=True, atroot=atroot)

    def _write(self, srcdir=None, append=False, atroot=None):
        mode = "w" if not append else "a"
        srcdir = self.src if srcdir is None else srcdir

        with zipfile.ZipFile(self.dst, mode) as zf:
            for dirname, _, files in os.walk(srcdir):
                for filename in files:
                    # Don't pack .pyc files unless asked to.
                    if self.skip_compiled and filename.endswith('.pyc'):
                        continue

                    _file = os.path.join(dirname, filename)
                    _arcfile = _file
                    if atroot:
                        _arcfile = os.path.join(atroot,
                                                os.path.relpath(_file, srcdir))
                    print ("Writing ", _file, " --> ", _arcfile)
                    zf.write(filename=_file, arcname=_arcfile)


if __name__ == '__main__':
    try:
        z = Zipper(output_file='lydian.egg')
        z.add_module('rpyc')
        z.add_module('sql30')
        # z.add_module('psutil')    # TODO : Resolve this.
        z.add_module('wavefront-sdk-python')
        z.add_module('wavefront-api-client')
        z.add_dir(dirname="lydian", atroot="./lydian/")
        logging.info("Generated sample.egg")
    except Exception as err:
        logging.info("Error in zipping directory")
