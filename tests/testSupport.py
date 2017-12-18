from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import PY3
import sys
import os
import tempfile
import shutil
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


class TempFile(object):

    """This context manager will deliver a pathname for a temporary file, and will
    remove it upon exit, if it indeed exists at that time. Note: it does _not_
    _create_ the temporary file.

        >>> with TempFile() as tmp:
        ...   assert not os.path.exists(tmp.path)
        ...   f = open(tmp.path, "wb")
        ...   b = f.write(b"hello.")
        ...   f.close()
        ...   assert os.path.exists(tmp.path)
        ...
        >>> assert not os.path.exists(tmp.path)
        >>> with TempFile(suffix=".png") as tmp:
        ...   assert tmp.path.endswith(".png")
        ...
    """

    _create = staticmethod(tempfile.mktemp)
    _destroy = staticmethod(os.remove)

    def __init__(self, suffix="", prefix="tmp", dir=None):
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.path = None

    def __enter__(self):
        self.path = self._create(suffix=self.suffix, prefix=self.prefix, dir=self.dir)
        return self

    def __exit__(self, type, value, traceback):
        if os.path.exists(self.path):
            self._destroy(self.path)


class TempFolder(TempFile):

    """This context manager will create a temporary folder, and will remove it upon exit.

        >>> with TempFolder() as tmp:
        ...   assert os.path.exists(tmp.path)
        ...   assert os.listdir(tmp.path) == []
        ...
        >>> assert not os.path.exists(tmp.path)
        >>> with TempFolder(suffix=".mystuff") as tmp:
        ...   assert tmp.path.endswith(".mystuff")
        ...
    """

    _create = staticmethod(tempfile.mkdtemp)
    _destroy = staticmethod(shutil.rmtree)


def randomSeed(a):
    if PY3:
        return random.seed(a, version=1)  # compatible with Python 2
    else:
        return random.seed(a)


def readData(path):
    """Return the raw data from a path."""
    with open(path, "rb") as f:
        return f.read()
