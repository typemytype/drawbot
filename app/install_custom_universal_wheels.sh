#!/bin/bash

set -e # abort on errors
set -x # echo commands


for package in pillow
do
	python app/build_universal_wheel.py $package
	pip install --force build/universal_wheels/$package*.whl
done
