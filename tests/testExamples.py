from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import sys
import os
import unittest
import re
import drawBot
from drawBot.drawBotDrawingTools import DrawBotDrawingTool
from testScripts import StdOutCollector


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
    pass


# The examples use an http image path; let's fake it with a local jpeg
testRoot = os.path.dirname(os.path.abspath(__file__))
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


def _makeTestCase(exampleName, source):

    def test(self):
        from drawBot.drawBotDrawingTools import _drawBotDrawingTool
        drawBot.newDrawing()
        code = compile(source, "<xxx>", "exec", dont_inherit=True)
        namespace = {}
        _drawBotDrawingTool._addToNamespace(namespace)
        namespace["image"] = mockImage
        namespace["imageSize"] = mockImageSize
        namespace["imagePixelColor"] = mockImagePixelColor
        with StdOutCollector(captureStdErr=True):
            exec(code, namespace)
        self.assertEquals(1, 1)

    return test


skip = {"test_variables", "test_printImage"}
expectedFailures = {"test_installFont"}

def _addExampleTests():
    allExamples = _collectExamples(DrawBotDrawingTool)
    for exampleName, source in allExamples.items():
        testMethod = _makeTestCase(exampleName, source)
        testMethod.__name__ = "test_%s" % exampleName
        if testMethod.__name__ in skip:
            continue
        if testMethod.__name__ in expectedFailures:
            testMethod = unittest.expectedFailure(testMethod)
        setattr(ExampleTester, testMethod.__name__, testMethod)

_addExampleTests()


if __name__ == "__main__":
    sys.exit(unittest.main())
