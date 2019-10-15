#!/bin/bash

set -e
set -x

python3 -m venv .venv-test/

source .venv-test/bin/activate

python3 -m pip install -r ./test-requirements.txt

python3 -m pip install -e .

python3 ./tests/runAllTests.py
