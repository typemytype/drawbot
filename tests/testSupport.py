from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import PY3
import sys
import os
import random
from drawBot.misc import warnings


testRootDir = os.path.dirname(os.path.abspath(__file__))
testDataDir = os.path.join(testRootDir, "data")
tempTestDataDir = os.path.join(testRootDir, "tempTestData")
if not os.path.exists(tempTestDataDir):
    os.mkdir(tempTestDataDir)


warnings.shouldShowWarnings = True


class StdOutCollector(list):

    def __init__(self, **kwargs):
        # force captureStdErr to be a keyword argument
        if kwargs:
            captureStdErr = kwargs["captureStdErr"]
            assert len(kwargs) == 1
        else:
            captureStdErr = False
        self.captureStdErr = captureStdErr
        super(StdOutCollector, self).__init__()

    def __enter__(self):
        self.out = sys.stdout
        self.err = sys.stderr
        sys.stdout = self
        if self.captureStdErr:
            sys.stderr = self
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self.out
        sys.stderr = self.err

    def write(self, txt):
        txt = txt.strip()
        if txt:
            self.append(txt)

    def flush(self):
        pass


def randomSeed(a):
    if PY3:
        return random.seed(a, version=1)  # compatible with Python 2
    else:
        return random.seed(a)


def readData(path):
    """Return the raw data from a path."""
    with open(path, "rb") as f:
        return f.read()
