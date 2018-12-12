#!/bin/bash

set -e
set -x

source .venv/bin/activate

# make sure drawBot is not installed as module
# py2app gets confused when building the app inside the package
python3 -m pip uninstall --yes drawBot
# build the app
python3 ./setupApp.py py2app --dmg
