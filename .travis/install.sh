#!/bin/bash

set -e
set -x

# install current python3 with homebrew
# NOTE: the formula is now named just "python"
brew update
if [[ $TRAVIS_OSX_IMAGE == 'xcode6.4' ]];
then
    brew install python
else
    brew upgrade python
fi

command -v python3
python3 --version
python3 -m pip install virtualenv
