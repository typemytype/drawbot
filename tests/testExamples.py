from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import sys
import os
import unittest
import re
import random
import drawBot
from drawBot.drawBotDrawingTools import DrawBotDrawingTool
from testScripts import StdOutCollector
from testSupport import randomSeed


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


def _collectExamples(module):
    allExamples = {}
    names = []
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

    def assertFilesEqual(self, path1, path2):
        self.assertEqual(readData(path1), readData(path2), "Files %r and %s are not the same" % (path1, path2))


def readData(path):
    # return the data from a path
    with open(path, "rb") as f:
        return f.read()



testRoot = os.path.dirname(os.path.abspath(__file__))
dataDir = os.path.join(testRoot, "data")
tempDataDir = os.path.join(testRoot, "temp_data")
# The examples use an http image path; let's fake it with a local jpeg
mockedImagePath = os.path.join(testRoot, "data", "drawBot.jpg")
assert os.path.exists(mockedImagePath)

def mockImage(path, position, alpha=1):
    import drawBot
    drawBot.image(mockedImagePath, position, alpha)

def mockImageSize(path):
    import drawBot
    return drawBot.imageSize(mockedImagePath)

def mockImagePixelColor(path, xy):
    import drawBot
    return drawBot.imagePixelColor(mockedImagePath, xy)

def mockVariable(definitions, namespace):
    for item in definitions:
        name = item["name"]
        args = item.get("args", {})
        value = args.get("value", 50)
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
        import __future__
        from drawBot.drawBotDrawingTools import _drawBotDrawingTool

        compileFlags = __future__.CO_FUTURE_DIVISION
        code = compile(source, "<%s>" % exampleName, "exec", flags=compileFlags, dont_inherit=True)

        namespace = {}
        _drawBotDrawingTool._addToNamespace(namespace)
        def mockSaveImage(path, **options):
            fileName = "example_mockSaveImage_" + os.path.basename(path)
            path = os.path.join(tempDataDir, fileName)
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
        imagePath = os.path.join(tempDataDir, fileName)
        expectedImagePath = os.path.join(dataDir, fileName)
        if doSaveImage:
            drawBot.saveImage(imagePath)
            self.assertFilesEqual(imagePath, expectedImagePath)

    return test


skip = {}
expectedFailures = {}
dontSaveImage = ["test_imageSize"]

def _addExampleTests():
    allExamples = _collectExamples(DrawBotDrawingTool)
    for exampleName, source in allExamples.items():
        testName = "test_%s" % exampleName
        testMethod = _makeTestCase(exampleName, source, doSaveImage=testName not in dontSaveImage)
        testMethod.__name__ = testName
        if testMethod.__name__ in skip:
            continue
        if testMethod.__name__ in expectedFailures:
            testMethod = unittest.expectedFailure(testMethod)
        setattr(ExampleTester, testMethod.__name__, testMethod)

_addExampleTests()


if __name__ == "__main__":
    sys.exit(unittest.main())
