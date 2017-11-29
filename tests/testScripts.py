from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import AppKit
import unittest
import os
import sys
import glob
import traceback


testRoot = os.path.dirname(os.path.abspath(__file__))
dataDir = os.path.join(testRoot, "data")
drawBotScriptDir = os.path.join(testRoot, "drawBotScripts")
tempDataDir = os.path.join(testRoot, "temp_data")
if not os.path.exists(tempDataDir):
    os.mkdir(tempDataDir)


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
            self.assertTrue(image1.TIFFRepresentation() == image2.TIFFRepresentation(), "PDF data on page %s is not the same" % (pageIndex + 1))

    def assertSVGFiles(self, path1, path2):
        # compare the content by line
        self.assertEqual(self.readData(path1).splitlines(), self.readData(path2).splitlines())

    def assertImageFiles(self, path1, path2):
        # compare the data and assert with a simple message
        # no use to show the complete diff of the binary file
        self.assertTrue(self.readData(path1) == self.readData(path2), "Images are not the same")

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
            source = f.read()
        code = compile(source, path, "exec")
        namespace = {"__name__": "__main__", "__file__": path}

        with StdOutCollector(captureStdErr=True) as output:
            try:
                exec(code, namespace)
            except:
                traceback.print_exc()
        return output

    def test_instructionStack(self):
        expected = [
            "reset None",
            "newPage 200 200",
            "save",
            "clipPath moveTo 5.0 5.0 lineTo 15.0 5.0 lineTo 15.0 15.0 lineTo 5.0 15.0 closePath",
            "restore",
            "image Image Object 10 10 0.5 None",
            "blendMode saturation",
            "transform 1 0 0 1 10 10",
            "drawPath moveTo 10.0 10.0 lineTo 110.0 10.0 lineTo 110.0 110.0 lineTo 10.0 110.0 closePath",
            "textBox foo bar 82.4829101562 84.0 35.0341796875 26.0 center",
            "frameDuration 10",
            "saveImage * None"
        ]
        with StdOutCollector() as output:
            import drawBot
            drawBot.newDrawing()
            drawBot.size(200, 200)
            drawBot.save()
            path = drawBot.BezierPath()
            path.rect(5, 5, 10, 10)
            drawBot.clipPath(path)
            drawBot.restore()
            im = drawBot.ImageObject()
            with im:
                drawBot.size(20, 20)
                drawBot.rect(5, 5, 10, 10)
            drawBot.image(im, (10, 10), alpha=.5)
            drawBot.blendMode("saturation")
            drawBot.translate(10, 10)
            drawBot.rect(10, 10, 100, 100)
            drawBot.text("foo bar", (100, 100), align="center")
            drawBot.frameDuration(10)
            drawBot.saveImage("*")
            drawBot.endDrawing()
        self.assertEqual(output, expected)


def cleanupTraceback(lines):
    """Strips the trace lines from a traceback. This assumes there is only one
    traceback in the list of lines.
    """
    tracebackIndex = None
    for i in range(len(lines)):
        if lines[i].startswith("Traceback (most recent call last):"):
            tracebackIndex = i
            break
    if tracebackIndex is not None:
        return lines[:tracebackIndex+1] + [lines[-1]]
    else:
        return lines


def readExpectedOutput(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return [l.strip() for l in f.read().splitlines()]
    else:
        return []


def makeTestCase(path, ext):
    module = os.path.basename(path)[:-3]

    def test(self):
        # get the paths
        testPath = os.path.join(tempDataDir, "%s.%s" % (module, ext))
        expectedPath = os.path.join(dataDir, "expected_%s.%s" % (module, ext))
        expectedOutputPath = os.path.join(dataDir, "expected_%s.txt" % module)
        expectedOutput = readExpectedOutput(expectedOutputPath)
        # get drawBot
        import drawBot
        # start a new drawing
        drawBot.newDrawing()
        # execute the script in place
        output = self.executeScriptPath(path)
        self.assertEqual(cleanupTraceback(output), cleanupTraceback(expectedOutput))
        # save the iamge
        drawBot.saveImage(testPath)
        # tell drawBot drawing is done
        drawBot.endDrawing()
        self.assertForFileExtension(ext, expectedPath, testPath)

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
    sys.exit(unittest.main())
