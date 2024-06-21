import unittest
import os
import sys
import glob
import warnings
from packaging.version import Version
from drawBot.macOSVersion import macOSVersion
from testSupport import DrawBotBaseTest, StdOutCollector, testRootDir, tempTestDataDir, testDataDir


drawBotScriptDir = os.path.join(testRootDir, "drawBotScripts")


class DrawBotTest(DrawBotBaseTest):

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
            "textBox foo bar 72.48291015625 86.0 55.0341796875 24.0 center",
            "frameDuration 10",
            "saveImage * {'myExtraArgument': True}"
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
            drawBot.saveImage("*", myExtraArgument=True)
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
    "test_svg_text2": (macOSVersion < Version("10.13"), "text as path comes out differently on 10.10"),
    "test_pdf_fontPath": (macOSVersion < Version("10.13"), "text as path comes out differently on 10.10"),
    "test_png_fontPath": (macOSVersion < Version("10.13"), "text as path comes out differently on 10.10"),
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
