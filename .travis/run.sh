#!/bin/bash

set -e
set -x

source .venv/bin/activate

python3 ./tests/runAllTests.py

python3 -m pip uninstall --yes drawBot
python3 ./setupApp.py py2app --dmg
