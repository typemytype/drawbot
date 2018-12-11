#!/bin/bash

set -e
set -x

echo "Install Start"

# install current python3 with homebrew
# NOTE: the formula is now named just "python"
# brew update
# brew upgrade python
command -v python3
python3 --version
python3 -m pip install virtualenv
python3 -m virtualenv .venv/

source .venv/bin/activate

echo "pip requirements"

python3 -m pip install ../requirements.txt
python3 -m setup.py install

echo "Install Done"
