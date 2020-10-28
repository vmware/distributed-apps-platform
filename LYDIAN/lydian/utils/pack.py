#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os
import tempfile


import lydian.apps.console as console

log = logging.getLogger(__name__)

def generate_egg(dest_dir, egg_name='lydian.egg'):
    """
    Packs lydian egg and places it in dest_dir.
    """

    reqs = [
            'rpyc==4.0.2',
            'sql30>=0.1.4',
            'psutil==5.6.6',
            'scapy==2.4.3',
            'wavefront-sdk-python>=1.1.1',
            'wavefront-api-client==2.33.15'
            ]
    commands = [
        'virtualenv -p python3 .',
        'pip install -r requirements.txt',
        'python -mzipper'
        ]

    with tempfile.mkstemp(prefix='lydian', dir='/tmp') as tdir:

        # Create requirements file.
        with open(os.path.join(tdir, 'requirements.txt'), 'w+') as fp:
            for req in req:
                fp.write(req + '\n')

        # Create Egg packing script.
        with open(os.path.join(tdir, 'run.sh'), 'w+') as fp:
            for line in commands:
                fp.write(line + '\n')

        zipper_path = os.path.join(
                os.path.basepath(os.path.abspath(__file__)),
                'zipper.py')

        dest_dir = os.path.join(os.getcwd(), dest_dir, egg_name)

        with console.Console(dir=tdir) as prompt:
            prompt.run('cp %s .' % zipper_path)
            prompt.run('sh -x run.sh')
            try:
                assert os.path.exists(os.path.join(tdir, egg_name))
                log.info("Created lydian egg")
                prompt.run('cp lydian.egg %s' % dest_dir)
            except AssertionError:
                log.error("Error in creating lydian egg")
