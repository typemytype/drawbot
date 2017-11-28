from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import AppKit
import unittest
import os
import glob


testRoot = os.path.dirname(os.path.abspath(__file__))
dataDir = os.path.join(testRoot, "data")
drawBotScriptDir = os.path.join(testRoot, "drawBotScripts")
tempDataDir = os.path.join(testRoot, "temp_data")
if not os.path.exists(tempDataDir):
    os.mkdir(tempDataDir)


class DrawBotTest(unittest.TestCase):

    def assertPDFFiles(self, path1, path2):
        # read as pdf document
        pdf1 = AppKit.PDFDocument.alloc().initWithURL_(AppKit.NSURL.fileURLWithPath_(path1))
        pdf2 = AppKit.PDFDocument.alloc().initWithURL_(AppKit.NSURL.fileURLWithPath_(path2))
        if pdf1 is None:
            # path1 is not a pdf document
            self.assertIsNone(pdf1)
        if pdf2 is None:
            # path2 is not a pdf document
            self.assertIsNone(pdf2)
        assert pdf1.pageCount() == pdf2.pageCount(), "PDFs has not the same amount of pages"
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
            assert image1.TIFFRepresentation() == image2.TIFFRepresentation(), "PDF data on page %s is not the same" % (pageIndex + 1)

    def assertSVGFiles(self, path1, path2):
        # compare the content by line
        self.assertEqual(self.readData(path1).splitlines(), self.readData(path2).splitlines())

    def assertImageFiles(self, path1, path2):
        # compare the data and assert with a simple message
        # no use to show the complete diff of the binary file
        assert self.readData(path1) == self.readData(path2), "Images are not the same"

    def assertGenericFiles(self, path1, path2):
        self.assertEqual(self.readData(path1), self.readData(path2))

    def assertForFileExtension(self, ext, path1, path2):
        # based on the ext choose an assertion test
        if ext == "pdf":
            self.assertPDFFiles(path1, path2)
        elif ext == "svg":
            self.assertSVGFiles(path1, path2)
        elif ext in ("png", "tiff", "jpeg", "jpg"):
            self.assertImageFiles(path1, path2)
        else:
            self.assertGenericFiles(path1, path2)

    def readData(self, path):
        # return the data from a path
        with open(path, "rb") as f:
            return f.read()

    def executeScriptPath(self, path):
        # read content of py file and exec it
        with open(path) as f:
            exec(f.read(), {})


def makeTestCase(path, ext):
    module = os.path.basename(path)[:-3]

    def test(self):
        # get the paths
        testPath = os.path.join(tempDataDir, "%s.%s" % (module, ext))
        expectedPath = os.path.join(dataDir, "expected_%s.%s" % (module, ext))
        # get drawBot
        import drawBot
        # start a new drawing
        drawBot.newDrawing()
        # execute the script in place
        self.executeScriptPath(path)
        # save the iamge
        drawBot.saveImage(testPath)
        # tell drawBot drawing is done
        drawBot.endDrawing()
        self.assertForFileExtension(ext, testPath, expectedPath)

    return test


testExt = [
    "svg",
    "png",
    "pdf"
]


for path in glob.glob(drawBotScriptDir + "/*.py"):
    for ext in testExt:
        testMethod = makeTestCase(path, ext)
        testMethod.__name__ = "test_%s_%s" % (ext, os.path.basename(path)[:-3])
        setattr(DrawBotTest, testMethod.__name__, testMethod)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
