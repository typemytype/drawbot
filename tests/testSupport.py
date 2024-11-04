import sys
import os
import tempfile
import unittest
import shutil
import random
import io
import traceback
import AppKit
from PIL import Image, ImageChops
from drawBot.misc import warnings


testRootDir = os.path.dirname(os.path.abspath(__file__))
testDataDir = os.path.join(testRootDir, "data")
tempTestDataDir = os.path.join(testRootDir, "tempTestData")
if not os.path.exists(tempTestDataDir):
    os.mkdir(tempTestDataDir)


warnings.shouldShowWarnings = True


class DrawBotBaseTest(unittest.TestCase):

    def assertPDFFilesEqual(self, path1, path2):
        # read as pdf document
        pdf1 = AppKit.PDFDocument.alloc().initWithURL_(AppKit.NSURL.fileURLWithPath_(path1))
        pdf2 = AppKit.PDFDocument.alloc().initWithURL_(AppKit.NSURL.fileURLWithPath_(path2))
        self.assertIsNotNone(pdf1, "PDF could not be read from %r" % path1)
        self.assertIsNotNone(pdf2, "PDF could not be read from %r" % path2)
        self.assertTrue(pdf1.pageCount() == pdf2.pageCount(), "PDFs has not the same amount of pages")
        # loop over all pages
        for pageIndex in range(pdf1.pageCount()):
            # get the pages
            page1 = pdf1.pageAtIndex_(pageIndex)
            page2 = pdf2.pageAtIndex_(pageIndex)
            # create images from the page data
            image1 = AppKit.NSImage.alloc().initWithData_(page1.dataRepresentation())
            image2 = AppKit.NSImage.alloc().initWithData_(page2.dataRepresentation())
            # compare the image tiff data
            # no use to show the complete diff of the binary data
            data1 = image1.TIFFRepresentation()
            data2 = image2.TIFFRepresentation()
            if data1 == data2:
                return  # all fine
            # Fall back to fuzzy image compare
            f1 = io.BytesIO(data1)
            f2 = io.BytesIO(data2)
            similarity = compareImages(f1, f2)
            self.assertLessEqual(similarity, 0.0011, "PDF files %r and %r are not similar enough: %s (page %s)" % (path1, path2, similarity, pageIndex + 1))

    def assertSVGFilesEqual(self, path1, path2):
        # compare the content by line
        self.assertEqual(readData(path1), readData(path2), "SVG files %r and %r are not identical" % (path1, path2))

    def assertImageFilesEqual(self, path1, path2):
        data1 = readData(path1)
        data2 = readData(path2)
        if data1 == data2:
            return  # all fine
        # Fall back to fuzzy image compare
        f1 = io.BytesIO(data1)
        f2 = io.BytesIO(data2)
        similarity = compareImages(f1, f2)
        self.assertLessEqual(similarity, 0.0011, "Images %r and %r are not similar enough: %s" % (path1, path2, similarity))

    def assertGenericFilesEqual(self, path1, path2):
        self.assertEqual(readData(path1), readData(path2))

    def assertForFileExtension(self, ext, path1, path2):
        # based on the ext choose an assertion test
        if ext == "pdf":
            self.assertPDFFilesEqual(path1, path2)
        elif ext == "svg":
            self.assertSVGFilesEqual(path1, path2)
        elif ext in ("png", "tiff", "jpeg", "jpg"):
            self.assertImageFilesEqual(path1, path2)
        else:
            self.assertGenericFilesEqual(path1, path2)

    def executeScriptPath(self, path):
        # read content of py file and exec it
        from drawBot.misc import warnings

        with open(path) as f:
            source = f.read()
        code = compile(source, path, "exec")
        namespace = {"__name__": "__main__", "__file__": path}
        warnings.resetWarnings()  # so we can test DB warnings

        with StdOutCollector(captureStdErr=True) as output:
            cwd = os.getcwd()
            os.chdir(os.path.dirname(path))
            try:
                exec(code, namespace)
            except Exception:
                traceback.print_exc()
            os.chdir(cwd)
        return output.lines()


class StdOutCollector:

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


class TempFile:

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
