#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os
import subprocess
import time
import tempfile


import lydian.apps.console as console
import lydian.utils.common as common_util

log = logging.getLogger(__name__)

class MyConsole(console.Console):

    def __init__(self, dir):
        super(MyConsole, self).__init__()
        self.cwd = dir

    def run(self, *args, **kwargs):
        kwargs['cwd'] = kwargs.get('cwd', self.cwd)
        return self.run_command(*args, **kwargs)

    def run_command(self, cmnd, env=None, cwd=None, timeout=-1, **kwargs):
        """
        run_command that passes on additional inputs to subprocess.
        """
        p = self._start_subprocess(cmnd=cmnd, cwd=cwd, env=env, **kwargs)

        # Start the counter for command to finish if requested.
        if timeout > 0:
            time_limit = time.time() + timeout

            while time.time() < time_limit:
                if self._is_alive(p):
                    time.sleep(1)
                else:
                    break
            self._kill_subprocess(p)

        stdout_val = p.communicate()[0]
        stdout_val = stdout_val.strip().decode('utf-8') if stdout_val else stdout_val
        return p.returncode, stdout_val

def generate_egg(dest_dir=None):
    """
    Packs lydian egg and places it in dest_dir.
    """
    data_dir = common_util.get_data_dir()
    egg_gen_file = 'generate_egg.sh'
    egg_name = 'lydian.egg'
    dest_dir = dest_dir or data_dir

    with tempfile.TemporaryDirectory(prefix='lydian_', dir='/tmp') as tdir:
        try:
            # Create requirements file.
            prompt = MyConsole(dir=tdir)
            prompt.run('cp %s .' % os.path.join(data_dir, egg_gen_file))
            prompt.run('sh -x %s' % egg_gen_file, stdout=subprocess.DEVNULL)
            assert os.path.exists(os.path.join(tdir, egg_name))
            log.info("Created lydian egg")
            prompt.run('cp lydian.egg %s' % dest_dir)
        except Exception:
            log.error("Error in creating lydian egg")


if __name__ == '__main__':
    generate_egg()