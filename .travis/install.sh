#!/bin/bash

set -e
set -x

echo "Install Start"

if [ "$TRAVIS_OS_NAME" == "osx" ]; then
    if [[ ${TOXENV} == *"py3"* ]]; then
        # install current python3 with homebrew
        # NOTE: the formula is now named just "python"
        brew update
        brew install python
        command -v python3
        python3 --version
        python3 -m pip install virtualenv
        python3 -m virtualenv .venv/
    else
        echo "unsupported $TOXENV: "${TOXENV}
        exit 1
    fi
    source .venv/bin/activate
fi

echo "pip requirements"

python -m pip install ../requirements.txt

echo "Install Done"