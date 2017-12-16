from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
from fontTools.misc.py23 import PY3
import sys
import unittest
import drawBot
from drawBot.misc import DrawBotError, warnings
from drawBot.scriptTools import ScriptRunner
from testScripts import StdOutCollector


class MiscTest(unittest.TestCase):

    def test_polygon_notEnoughPoints(self):
        drawBot.newDrawing()
        with self.assertRaises(TypeError):
            drawBot.polygon()
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2))
        drawBot.polygon((1, 2), (3, 4))

    def test_polygon_unexpectedKeywordArgument(self):
        drawBot.newDrawing()
        drawBot.polygon((1, 2), (3, 4), close=True)
        drawBot.polygon((1, 2), (3, 4), close=False)
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2), (3, 4), closed=False)
        with self.assertRaises(TypeError):
            drawBot.polygon((1, 2), (3, 4), closed=False, foo=123)

    def test_ScriptRunner_StdOutCollector(self):
        #import io
        #out = io.BytesIO()
        #ScriptRunner(u"print('hey!')", stdout=out, stderr=out)
        #self.assertEqual(out.getvalue(), "hey!\n")
        out = StdOutCollector()
        ScriptRunner("print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out, ["hey!"])

    def test_ScriptRunner_print_function(self):
        out = StdOutCollector()
        ScriptRunner("print 'hey!'", stdout=out, stderr=out)
        if PY3:
            self.assertEqual(out[-1], "SyntaxError: Missing parentheses in call to 'print'. Did you mean print('hey!')?")
        else:
            self.assertEqual(out, ["hey!"])


if __name__ == '__main__':
    sys.exit(unittest.main())
