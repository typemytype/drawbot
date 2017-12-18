from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import AppKit
import unittest
import os
import sys
import glob
import traceback
import warnings
from testSupport import StdOutCollector, randomSeed, testRootDir, tempTestDataDir, testDataDir, readData


drawBotScriptDir = os.path.join(testRootDir, "drawBotScripts")


class DrawBotTest(unittest.TestCase):

    def assertPDFFilesEqual(self, path1, path2):
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

    def assertSVGFilesEqual(self, path1, path2):
        # compare the content by line
        self.assertEqual(readData(path1), readData(path2))

    def assertImageFilesEqual(self, path1, path2):
        # compare the data and assert with a simple message
        # no use to show the complete diff of the binary file
        self.assertTrue(readData(path1) == readData(path2), "Images are not the same")

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
        import __future__
        with open(path) as f:
            source = f.read()
        compileFlags = __future__.CO_FUTURE_DIVISION
        code = compile(source, path, "exec", flags=compileFlags, dont_inherit=True)
        namespace = {"__name__": "__main__", "__file__": path}

        with StdOutCollector(captureStdErr=True) as output:
            cwd = os.getcwd()
            os.chdir(os.path.dirname(path))
            try:
                exec(code, namespace)
            except:
                traceback.print_exc()
            os.chdir(cwd)
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
            "textBox foo bar 82.4829102 84.0 35.0341797 26.0 center",
            "frameDuration 10",
            "saveImage * {'myExtraAgrument': True}"
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
            drawBot.saveImage("*", myExtraAgrument=True)
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


def makeTestCase(path, ext, ignoreDeprecationWarnings):
    scriptName = os.path.basename(path)[:-3]

    def test(self):
        # get the paths
        testPath = os.path.join(tempTestDataDir, "%s.%s" % (scriptName, ext))
        expectedPath = os.path.join(testDataDir, "expected_%s.%s" % (scriptName, ext))
        expectedOutputPath = os.path.join(testDataDir, "expected_%s.txt" % scriptName)
        expectedOutput = readExpectedOutput(expectedOutputPath)
        # get drawBot
        import drawBot
        # start a new drawing
        drawBot.newDrawing()
        # execute the script in place
        # temporarily ignore deprecation warnings (there are some from PyObjC :( )
        with warnings.catch_warnings():
            if ignoreDeprecationWarnings:
                warnings.simplefilter("ignore", DeprecationWarning)
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


expectedFailures = {}
ignoreDeprecationWarnings = {
    # there are some pesky PyObjC warnings that interfere with our stdout/stderr capturing,
    # like: 'DeprecationWarning: Using struct wrapper as sequence'
    "test_pdf_image3",
    "test_pdf_image4",
    "test_pdf_text",
    "test_png_image3",
    "test_png_image4",
    "test_png_text",
    "test_svg_image3",
    "test_svg_image4",
    "test_svg_text",
}

def _addTests():
    for path in glob.glob(os.path.join(drawBotScriptDir, "*.py")):
        scriptName = os.path.splitext(os.path.basename(path))[0]
        for ext in testExt:
            testMethodName = "test_%s_%s" % (ext, scriptName)
            testMethod = makeTestCase(path, ext, testMethodName in ignoreDeprecationWarnings)
            testMethod.__name__ = testMethodName
            if testMethod.__name__ in expectedFailures:
                testMethod = unittest.expectedFailure(testMethod)
            setattr(DrawBotTest, testMethod.__name__, testMethod)

_addTests()


if __name__ == '__main__':
    sys.exit(unittest.main())
