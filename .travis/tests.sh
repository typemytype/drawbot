#!/bin/bash

set -e
set -x

python3 -m virtualenv .venv-test/

source .venv-test/bin/activate

python3 -m pip install -r ./test-requirements.txt

python3 setup.py install

python3 ./tests/runAllTests.py