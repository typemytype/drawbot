#!/bin/bash

set -e # abort on errors
set -x # echo commands


for package_version in pillow==10.1.0
do
	package=(${package_version//==/ })
	python app/build_universal_wheel.py $package_version
	pip install --force build/universal_wheels/$package*.whl
done
