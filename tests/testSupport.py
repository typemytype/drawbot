from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import PY3
import random


def randomSeed(a):
    if PY3:
        return random.seed(a, version=1)  # compatible with Python 2
    else:
        return random.seed(a)
