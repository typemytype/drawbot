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
