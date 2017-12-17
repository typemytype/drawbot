from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import PY3
import os
import random


testRootDir = os.path.dirname(os.path.abspath(__file__))
testDataDir = os.path.join(testRootDir, "data")
tempTestDataDir = os.path.join(testRootDir, "temp_data")
if not os.path.exists(tempTestDataDir):
    os.mkdir(tempTestDataDir)


def randomSeed(a):
    if PY3:
        return random.seed(a, version=1)  # compatible with Python 2
    else:
        return random.seed(a)
