#!/bin/sh
# Generates egg
virtualenv -p python3 .
mkdir unpacked
source bin/activate
bin/pip install --target=./unpacked/ lydian
cd unpacked
zip -r9 ../lydian.egg *
cd -
