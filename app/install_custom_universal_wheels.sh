#!/bin/bash

set -e # abort on errors


python app/build_universal_wheel.py pillow

pip install --force build/universal_wheels/pillow*.whl
