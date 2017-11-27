from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import unittest
import os

testRoot = os.path.dirname(os.path.abspath(__file__))
dataDir = os.path.join(testRoot, "data")
tempDataDir = os.path.join(testRoot, "temp_data")
if not os.path.exists(tempDataDir):
    os.mkdir(tempDataDir)


class ShapesTestCase(unittest.TestCase):

    def makeTestDrawing(self):
        from drawBot import newDrawing, size, rect, oval, fill, stroke, strokeWidth
        newDrawing()
        size(200, 200)
        fill(0)
        rect(10, 10, 100, 100)
        fill(0, 1, 0)
        stroke(1, 0, 0)
        strokeWidth(5)
        oval(50, 50, 100, 100)

    def test_svg(self):
        from drawBot import saveImage
        self.makeTestDrawing()
        svgPath = os.path.join(tempDataDir, "shapes.svg")
        saveImage(svgPath)
        expectedPath = os.path.join(dataDir, "expected_shapes.svg")
        self.assertEqual(readTextData(svgPath), readTextData(expectedPath))


def readTextData(path):
    with open(path) as f:
        return f.read()


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
