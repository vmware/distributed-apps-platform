#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
A simple module for zipping files and creating egg files.
'''
import importlib
import logging
import os
import tempfile
import time
import zipfile

log = logging.getLogger(__name__)


class Zipper(object):
    EXPAND_LINKS = True
    SKIP_COMPILED = True

    def __init__(self, output_file, source=None, verbose=False):
        # Output file with path
        self.dst = output_file

        # input source for zipping
        self.src = source

        self.modules = []

        # skip compiled code
        self.skip_compiled = self.SKIP_COMPILED

        self.verbose = verbose or os.environ.get('LYDIAN_VERBOSE', False)

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
                    # print ("Writing ", _file, " --> ", _arcfile)
                    if self.verbose:
                        log.debug("Writing %s --> %s", _file, _arcfile)
                    zf.write(filename=_file, arcname=_arcfile)


def install_egg():
    """
    Installs egg in Lydian package.
    """
    lydian_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../'))
    install_dir = os.path.join(lydian_path, 'data')

    lock_file = os.path.join(install_dir, 'install.lock')
    # Locking mechanism
    while os.path.exists(lock_file):
        log.info("Waiting for other egg installation to finish.")
        time.sleep(7)

    egg_file = os.path.join(install_dir, 'lydian.egg')
    if os.path.exists(egg_file):
        log.info("Egg already installed. Creation skipped.")
        return

    try:
        temp_egg_file = tempfile.NamedTemporaryFile(dir='/tmp',
            prefix='lydian_egg_', suffix='.egg', delete=False)

        # Create Lock file
        # TODO : Following is still not a full proof locking
        # mechanism. If preparing of hosts need to go parallel
        # this needs to be done in a better way.
        with open(lock_file, 'w+') as _:
            _ = _

        z = Zipper(output_file=temp_egg_file.name)

        # Pack Lydian dependency packages.
        z.add_module('rpyc')
        z.add_module('sql30')

        # Pack Lydian Source
        z.add_dir(dirname=lydian_path, atroot="./lydian/")
        os.system('cp %s %s' % (temp_egg_file.name, egg_file))
        logging.info("Generated local egg at %s", egg_file)
    except Exception as err:
        logging.info("Error in zipping directory :%r", err)
    finally:
        # release lock file
        if os.path.exists(lock_file):
            os.remove(lock_file)

        if os.path.exists(temp_egg_file.name):
            os.remove(temp_egg_file.name)


if __name__ == '__main__':
    install_egg()

