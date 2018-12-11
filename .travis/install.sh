#!/bin/bash

set -e
set -x

# install current python3 with homebrew
# NOTE: the formula is now named just "python"
# brew update
# brew upgrade python
command -v python3
python3 --version
python3 -m pip install virtualenv
python3 -m virtualenv .venv/

source .venv/bin/activate

python3 -m pip install -r ./requirements.txt
python3 -m pip install -r ./test-requirements.txt

python3 setup.py install