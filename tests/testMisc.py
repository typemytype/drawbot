from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import sys
import unittest
import drawBot
from drawBot.misc import DrawBotError, warnings


class MiscTest(unittest.TestCase):

    def test_polygon_noPoints(self):
        drawBot.newDrawing()
        with self.assertRaises(TypeError):
            drawBot.polygon()

    def test_polygon_unexpectedKeywordArgument(self):
        drawBot.newDrawing()
        drawBot.polygon((1, 2), (3, 4), close=True)
        drawBot.polygon((1, 2), (3, 4), close=False)
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2), (3, 4), closed=False)
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2), (3, 4), closed=False, foo=123)


if __name__ == '__main__':
    sys.exit(unittest.main())
