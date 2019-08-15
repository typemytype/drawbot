import sys
import os
import tempfile
import shutil
import random
import io
from PIL import Image, ImageChops
from drawBot.misc import warnings


testRootDir = os.path.dirname(os.path.abspath(__file__))
testDataDir = os.path.join(testRootDir, "data")
tempTestDataDir = os.path.join(testRootDir, "tempTestData")
if not os.path.exists(tempTestDataDir):
    os.mkdir(tempTestDataDir)


warnings.shouldShowWarnings = True


class StdOutCollector(object):

    def __init__(self, **kwargs):
        # force captureStdErr to be a keyword argument
        if kwargs:
            captureStdErr = kwargs["captureStdErr"]
            assert len(kwargs) == 1
        else:
            captureStdErr = False
        self.captureStdErr = captureStdErr
        self._stream = io.StringIO()

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
        self._stream.write(txt)

    def flush(self):
        pass

    def lines(self):
        return self._stream.getvalue().splitlines()


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
    return random.seed(a, version=1)  # compatible with Python 2


def readData(path):
    """Return the raw data from a path."""
    with open(path, "rb") as f:
        return f.read()


def compareImages(path1, path2):
    """Compare two image files and return a number representing how similar they are.
    A value of 0 means that the images are identical, a value of 1 means they are maximally
    different or not comparable (for example, when their dimensions differ).
    """
    im1 = Image.open(path1)
    im2 = Image.open(path2)

    if im1.size != im2.size:
        # Dimensions differ, can't compare further
        return 1

    if im1 == im2:
        # Image data is identical (I checked PIL's Image.__eq__ method: it's solid)
        return 0

    # Get the difference between the images
    diff = ImageChops.difference(im1, im2)

    # We'll calculate the average difference based on the histogram provided by PIL
    hist = diff.histogram()
    assert len(hist) == 4 * 256  # Assuming 4x8-bit RGBA for now. TODO: make this work for L and RGB modes
    # Sum the histograms of each channel
    summedHist = [sum(hist[pixelValue + ch * 256] for ch in range(4)) for pixelValue in range(256)]

    assert len(summedHist) == 256
    assert sum(hist) == sum(summedHist)
    # Calculate the average of the difference
    # First add all pixel values together
    totalSum = sum(summedHist[pixelValue] * pixelValue for pixelValue in range(256))
    # Then divide by the total number of channel values
    average = totalSum / sum(summedHist)
    # Scale pixel value range from 0-255 to 0-1
    average = average / 255
    assert 0.0 <= average <= 1.0
    return average
