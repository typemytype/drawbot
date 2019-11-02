import sys
import os
import unittest
import re
import random
import AppKit
import drawBot
from drawBot.drawBotDrawingTools import DrawBotDrawingTool
from testSupport import StdOutCollector, randomSeed, testRootDir, tempTestDataDir, testDataDir, readData, compareImages


_namePattern = re.compile(r"( +).. downloadcode:: ([A-Za-z0-9_]+).py\s*$")
_indentPattern = re.compile(r"( +)")

def _dedent(lines):
    minIndentation = 10000
    for line in lines:
        if not line.strip():
            continue
        m = _indentPattern.match(line)
        if m is not None:
            minIndentation = min(minIndentation, len(m.group(1)))
    assert minIndentation < 10000
    return [line[minIndentation:] for line in lines]


def _collectExamples(modules):
    allExamples = {}
    names = []
    for module in modules:
        for n in module.__dict__:
            code = None
            name = None
            indentation = None
            if n[0] != "_":
                method = getattr(module, n)
                if method.__doc__ and "downloadcode" in method.__doc__:
                    for line in method.__doc__.splitlines() + ["."]:
                        assert "\t" not in line, (name, repr(line))
                        if code is None:
                            m = _namePattern.match(line)
                            if m is not None:
                                name = m.group(2)
                                # print(name)
                                names.append(name)
                                indentation = len(m.group(1))
                                code = []
                        else:
                            if not line.strip() and not code:
                                continue
                            m = _indentPattern.match(line)
                            if line.strip() and (m is None or len(m.group(1)) <= indentation):
                                assert name not in allExamples
                                allExamples[name] = "\n".join(_dedent(code))
                                name = None
                                code = None
                                indentation = None
                            else:
                                code.append(line)
    return allExamples


class ExampleTester(unittest.TestCase):

    def assertImagesSimilar(self, path1, path2):
        similarity = compareImages(path1, path2)
        self.assertLessEqual(similarity, 0.0012, "Images %r and %s are not similar enough: %s" % (path1, path2, similarity))


# The examples use an http image path; let's fake it with a local jpeg
mockedImagePath = os.path.join(testRootDir, "data", "drawBot.jpg")
assert os.path.exists(mockedImagePath)

def mockImage(path, position, alpha=1):
    if isinstance(path, DrawBotDrawingTool._imageClass):
        drawBot.image(path, position, alpha)
    else:
        drawBot.image(mockedImagePath, position, alpha)

def mockImageSize(path):
    return drawBot.imageSize(mockedImagePath)

def mockImagePixelColor(path, xy):
    return drawBot.imagePixelColor(mockedImagePath, xy)

def mockVariable(definitions, namespace):
    for item in definitions:
        name = item["name"]
        args = item.get("args", {})
        value = args.get("value", None)
        if value is None:
            # no value is set
            uiElement = item["ui"]
            if uiElement == "ColorWell":
                # in case of a color well
                # the default color is black nscolor object
                value = AppKit.NSColor.blackColor()
            elif uiElement == "Checkbox":
                # the default is off
                value = False
            else:
                # fallback to slider value
                value = 50
        namespace[name] = value

def mockPrintImage(pdf=None):
    pass

def mockInstallFont(path):
    return "Helvetica"

def mockUninstallFont(path):
    pass

def mockRandInt(lo, hi):
    # For compatibility between Python 2 and 3
    hi += 1
    assert lo < hi
    extent = hi - lo
    return int(lo + extent * random.random())


def _makeTestCase(exampleName, source, doSaveImage):

    def test(self):
        from drawBot.drawBotDrawingTools import _drawBotDrawingTool

        code = compile(source, "<%s>" % exampleName, "exec")

        namespace = {}
        _drawBotDrawingTool._addToNamespace(namespace)
        def mockSaveImage(path, **options):
            fileName = "example_mockSaveImage_" + os.path.basename(path)
            path = os.path.join(tempTestDataDir, fileName)
            drawBot.saveImage(path, **options)
        namespace["saveImage"] = mockSaveImage
        namespace["image"] = mockImage
        namespace["imageSize"] = mockImageSize
        namespace["imagePixelColor"] = mockImagePixelColor
        namespace["Variable"] = mockVariable
        namespace["printImage"] = mockPrintImage
        namespace["installFont"] = mockInstallFont
        namespace["uninstallFont"] = mockUninstallFont
        namespace["randint"] = mockRandInt

        randomSeed(0)
        drawBot.newDrawing()
        with StdOutCollector(captureStdErr=True):
            exec(code, namespace)
        fileName = "example_%s.png" % exampleName
        imagePath = os.path.join(tempTestDataDir, fileName)
        expectedImagePath = os.path.join(testDataDir, fileName)
        if doSaveImage:
            drawBot.saveImage(imagePath)
            self.assertImagesSimilar(imagePath, expectedImagePath)

    return test


skip = {
    "test_imageObject",  # skipping, the rendering diff between OS versions is too great
    "test_lineHeight",  # This fails on Travis. TODO: figure out why.
}
expectedFailures = {}
dontSaveImage = {"test_imageSize"}

def _addExampleTests():
    allExamples = _collectExamples([
        DrawBotDrawingTool,
        DrawBotDrawingTool._formattedStringClass,
        DrawBotDrawingTool._bezierPathClass,
        DrawBotDrawingTool._imageClass
    ])

    for exampleName, source in allExamples.items():
        testMethodName = "test_%s" % exampleName
        testMethod = _makeTestCase(exampleName, source, doSaveImage=testMethodName not in dontSaveImage)
        testMethod.__name__ = testMethodName
        if testMethodName in expectedFailures:
            testMethod = unittest.expectedFailure(testMethod)
        if testMethodName in skip:
            testMethod = unittest.skip("manual skip")(testMethod)
        setattr(ExampleTester, testMethodName, testMethod)

_addExampleTests()


if __name__ == "__main__":
    sys.exit(unittest.main())
