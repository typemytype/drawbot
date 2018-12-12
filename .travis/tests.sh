#!/bin/bash

set -e
set -x

source .venv/bin/activate

python3 ./tests/runAllTests.py