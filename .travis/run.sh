#!/bin/bash

set -e
set -x

echo "Script Start"

echo "Run Tests"
python3 ./tests/runAllTests.py

echo "Build App"
python3 ./setupApp.py py2app

echo "Script Done"
