from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
from fontTools.misc.py23 import PY3
import sys
import os
import unittest
import io
from collections import OrderedDict
import drawBot
from drawBot.misc import DrawBotError, warnings
from drawBot.scriptTools import ScriptRunner
from testSupport import StdOutCollector, testDataDir


class MiscTest(unittest.TestCase):

    def test_openTypeFeatures(self):
        drawBot.newDrawing()
        fea = drawBot.listOpenTypeFeatures()
        self.assertEqual(fea, {'liga': True})
        drawBot.font("Helvetica")
        fea = drawBot.listOpenTypeFeatures()
        self.assertEqual(fea, {'liga': True, 'tnum': True, 'pnum': False})
        fea = drawBot.listOpenTypeFeatures("HoeflerText-Regular")
        self.assertEqual(fea, {'liga': True, 'dlig': False, 'tnum': True, 'pnum': False, 'titl': True, 'onum': True, 'lnum': False})
        fea = drawBot.openTypeFeatures(liga=False)
        self.assertEqual(fea, {'liga': False, 'tnum': True, 'pnum': False})
        drawBot.font("LucidaGrande")
        fea = drawBot.openTypeFeatures(resetFeatures=True)
        self.assertEqual(fea, {'liga': True})

    def test_openTypeFeatures_saveRestore(self):
        drawBot.newDrawing()
        drawBot.font("AppleBraille")
        drawBot.save()
        drawBot.restore()

    def test_fontVariations(self):
        drawBot.newDrawing()
        var = drawBot.listFontVariations()
        self.assertEqual(var, {})
        drawBot.font("Skia")
        # get the default font variations
        var = drawBot.listFontVariations()
        expectedVar = OrderedDict({'wght': {'name': 'Weight', 'minValue': 0.4799, 'maxValue': 3.1999, 'defaultValue': 1.0}, 'wdth': {'name': 'Width', 'minValue': 0.6199, 'maxValue': 1.3, 'defaultValue': 1.0}})
        self.assertEqual(var, expectedVar)
        # set a font variation
        var = drawBot.fontVariations(wght=5)
        expectedVarChanged = {'wght': 5, 'wdth': 1.0}
        self.assertEqual(var, expectedVarChanged)
        # clear all font variations settings
        var = drawBot.fontVariations(resetVariations=True)
        self.assertEqual(var, {'wght': 1.0, 'wdth': 1.0})
        drawBot.font("Helvetica")
        var = drawBot.listFontVariations()
        self.assertEqual(var, {})
        var = drawBot.fontVariations(wght=5)
        self.assertEqual(var, {"wght": 5})

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

    def test_image_imageResolution(self):
        path = os.path.join(testDataDir, "drawbot.png")
        dpi = drawBot.imageResolution(path)
        self.assertEqual(dpi, 72)

        path = os.path.join(testDataDir, "drawbot144.png")
        dpi = drawBot.imageResolution(path)
        self.assertEqual(dpi, 144)

    def test_ScriptRunner_StdOutCollector(self):
        out = StdOutCollector()
        ScriptRunner("print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out.lines(), ["hey!"])

    def test_ScriptRunner_io(self):
        if PY3:
            MyStringIO = io.StringIO
        else:
            class MyStringIO(io.StringIO):
                def write(self, value):
                    if not isinstance(value, unicode):
                        value = value.decode("utf8")
                    super(MyStringIO, self).write(value)
        out = MyStringIO()
        ScriptRunner("print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = MyStringIO()
        ScriptRunner("print(u'hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = MyStringIO()
        ScriptRunner(u"print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = MyStringIO()
        ScriptRunner(u"print(u'hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')

    def test_ScriptRunner_print_function(self):
        out = StdOutCollector()
        ScriptRunner("print 'hey!'", stdout=out, stderr=out)
        if PY3:
            self.assertEqual(out.lines()[-1], "SyntaxError: Missing parentheses in call to 'print'. Did you mean print('hey!')?")
        else:
            self.assertEqual(out.lines(), ["hey!"])

    def test_ScriptRunner_division(self):
        out = StdOutCollector()
        ScriptRunner("print(1/2)", stdout=out, stderr=out)
        self.assertEqual(out.lines(), ["0.5"])

    def test_ScriptRunner_oldDivision(self):
        realGetDefault = drawBot.scriptTools.getDefault
        def mockedGetDefault(*args):
            return False
        drawBot.scriptTools.getDefault = mockedGetDefault
        try:
            out = StdOutCollector()
            ScriptRunner("print(1/2)", stdout=out, stderr=out)
            if PY3:
                self.assertEqual(out.lines(), ["0.5"])
            else:
                self.assertEqual(out.lines(), ["0"])
        finally:
            drawBot.scriptTools.getDefault = realGetDefault

    def test_ScriptRunner_encoding(self):
        out = StdOutCollector()
        ScriptRunner("# -*- coding: utf-8 -*-\nprint(1/2)", stdout=out, stderr=out)
        self.assertEqual(out.lines(), ["0.5"])
        out = StdOutCollector()
        ScriptRunner(u"# -*- coding: utf-8 -*-\nprint(1/2)", stdout=out, stderr=out)
        self.assertEqual(out.lines(), ["0.5"])

    def test_ScriptRunner_file(self):
        out = StdOutCollector()
        path = os.path.join(testDataDir, "scriptRunnerTest.py") # use an actual file, no not confuse coverage testing
        ScriptRunner("print(__file__)\nprint(__name__)", stdout=out, stderr=out, path=path)
        self.assertEqual(out.lines(), [path, "__main__"])

    def test_ScriptRunner_fromPath(self):
        out = StdOutCollector()
        path = os.path.join(testDataDir, "scriptRunnerTest.py")
        ScriptRunner(path=path, stdout=out, stderr=out)
        self.assertEqual(out.lines(), [path, "__main__", u'\xc5benr\xe5'])

    def test_ScriptRunner_namespace(self):
        out = StdOutCollector()
        ScriptRunner("print(aaaa)", stdout=out, stderr=out, namespace=dict(aaaa=123))
        self.assertEqual(out.lines(), ["123"])

    def test_ScriptRunner_checkSyntaxOnly(self):
        out = StdOutCollector()
        ScriptRunner("print(aaaa)", stdout=out, stderr=out, checkSyntaxOnly=True)
        self.assertEqual(out.lines(), [])
        out = StdOutCollector()
        ScriptRunner("print('hello world!')", stdout=out, stderr=out, checkSyntaxOnly=False)
        self.assertEqual(out.lines(), ['hello world!'])
        out = StdOutCollector()
        ScriptRunner("print('hello world!')", stdout=out, stderr=out, checkSyntaxOnly=True)
        self.assertEqual(out.lines(), [])
        out = StdOutCollector()
        ScriptRunner("aaa bbb", stdout=out, stderr=out, checkSyntaxOnly=True)
        self.assertEqual(out.lines()[-1], 'SyntaxError: invalid syntax')

    def test_newPage_empty_single(self):
        drawBot.newDrawing()
        drawBot.newPage()
        self.assertEqual(drawBot.width(), 1000)
        self.assertEqual(drawBot.height(), 1000)
        self.assertEqual(drawBot.pageCount(), 1)

    def test_newPage_empty_implicit_first_page(self):
        drawBot.newDrawing()
        drawBot.rect(100, 100, 200, 200)
        drawBot.newPage()
        self.assertEqual(drawBot.width(), 1000)
        self.assertEqual(drawBot.height(), 1000)
        self.assertEqual(drawBot.pageCount(), 2)

    def test_newPage_empty_multiple(self):
        drawBot.newDrawing()
        drawBot.newPage()
        drawBot.newPage()
        drawBot.newPage()
        self.assertEqual(drawBot.width(), 1000)
        self.assertEqual(drawBot.height(), 1000)
        self.assertEqual(drawBot.pageCount(), 3)

    def test_newPage_following(self):
        drawBot.newDrawing()
        drawBot.size(400, 500)
        drawBot.newPage()
        self.assertEqual(drawBot.width(), 400)
        self.assertEqual(drawBot.height(), 500)
        self.assertEqual(drawBot.pageCount(), 2)


if __name__ == '__main__':
    sys.exit(unittest.main())
