import AppKit
import io
import unittest
import os
import sys
import glob
import traceback
import warnings
from drawBot.macOSVersion import macOSVersion
from testSupport import StdOutCollector, randomSeed, testRootDir, tempTestDataDir, testDataDir, readData, compareImages


drawBotScriptDir = os.path.join(testRootDir, "drawBotScripts")


class DrawBotTest(unittest.TestCase):

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
        self.assertTrue(readData(path1) == readData(path2), "SVG files %r and %r are not identical" % (path1, path2))

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
            except:
                traceback.print_exc()
            os.chdir(cwd)
        return output.lines()

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
            "textBox foo bar 72.48291015625 84.0 55.0341796875 26.0 center",
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
        self.assertEqual(output.lines(), expected)

    def test_booleanoperationListIntersections(self):
        expected = [(75, 150), (150, 75)]
        import drawBot
        path1 = drawBot.BezierPath()
        path1.rect(50, 50, 100, 100)
        path2 = drawBot.BezierPath()
        path2.rect(75, 75, 100, 100)
        result = path1.intersectionPoints(path2)
        self.assertEqual(sorted(result), sorted(expected))
        path1.appendPath(path2)
        result = path1.intersectionPoints()
        self.assertEqual(sorted(result), sorted(expected))


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
            return [l for l in f.read().splitlines()]
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
        # save the image
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


skipTests = {
    "test_pdf_fontVariations2",  # Fails on 10.13 on Travis, why?
    "test_png_fontVariations2",  # Fails on 10.13 on Travis, why?
    "test_svg_fontVariations2",  # On macOS 10.13, there is a named instance for Condensed. Also, Variable fonts don't work in SVG export yet.
    "test_svg_fontVariations",  # on macOS 10.15 the family name of the font contains the location: 'Skia-Regular_wght9999_wdth10000'.
    "test_svg_image3",  # embedded image is subtly different, but we can't render SVG, so we can't compare fuzzily
    "test_svg_image4",  # ditto.
    "test_svg_fontPath",  # no fonts embedded into svg and no var support (yet)
}

conditionalSkip = {
    "test_svg_text2": (macOSVersion < "10.13", "text as path comes out differently on 10.10"),
    "test_pdf_fontPath": (macOSVersion < "10.13", "text as path comes out differently on 10.10"),
    "test_png_fontPath": (macOSVersion < "10.13", "text as path comes out differently on 10.10"),
}

expectedFailures = {}

ignoreDeprecationWarnings = {
    # there are some pesky PyObjC warnings that interfere with our stdout/stderr capturing,
    # like: 'DeprecationWarning: Using struct wrapper as sequence'
    "test_pdf_fontVariations",
    "test_pdf_image3",
    "test_pdf_image4",
    "test_pdf_openTypeFeatures",
    "test_pdf_text",
    "test_png_fontVariations",
    "test_png_image3",
    "test_png_image4",
    "test_png_openTypeFeatures",
    "test_png_text",
    "test_svg_fontVariations",
    "test_svg_image3",
    "test_svg_image4",
    "test_svg_openTypeFeatures",
    "test_svg_text",
    "test_pdf_imagePixelColor",
    "test_png_imagePixelColor",
    "test_svg_imagePixelColor",
}

def _addTests():
    for path in glob.glob(os.path.join(drawBotScriptDir, "*.py")):
        scriptName = os.path.splitext(os.path.basename(path))[0]
        for ext in testExt:
            testMethodName = "test_%s_%s" % (ext, scriptName)
            testMethod = makeTestCase(path, ext, testMethodName in ignoreDeprecationWarnings)
            testMethod.__name__ = testMethodName
            if testMethodName in expectedFailures:
                testMethod = unittest.expectedFailure(testMethod)
            if testMethodName in skipTests:
                testMethod = unittest.skip("manual skip")(testMethod)
            if testMethodName in conditionalSkip:
                testMethod = unittest.skipIf(*conditionalSkip[testMethodName])(testMethod)
            setattr(DrawBotTest, testMethodName, testMethod)

_addTests()


if __name__ == '__main__':
    sys.exit(unittest.main())
