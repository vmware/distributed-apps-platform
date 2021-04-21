#!/bin/sh
python -m unittest discover -p test_background.py lydian/tests/common
python -m unittest discover -p test_mocktraffic.py lydian/tests/integration
