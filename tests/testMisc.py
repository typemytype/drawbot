import sys
import os
import unittest
import io
from collections import OrderedDict
import drawBot
from drawBot.misc import DrawBotError, warnings
from drawBot.scriptTools import ScriptRunner
from testSupport import StdOutCollector, testDataDir


def _roundDictValues(d, digits):
    return {k: round(v, digits) if isinstance(v, float) else v for k, v in d.items()}


class MiscTest(unittest.TestCase):

    def test_openTypeFeatures(self):
        drawBot.newDrawing()
        fea = drawBot.listOpenTypeFeatures()
        self.assertEqual(fea, ['liga'])
        drawBot.font("Helvetica")
        fea = drawBot.listOpenTypeFeatures()
        self.assertEqual(fea, ['liga', 'pnum', 'tnum'])
        fea = drawBot.listOpenTypeFeatures("HoeflerText-Regular")
        self.assertEqual(fea, ['dlig', 'liga', 'lnum', 'onum', 'pnum', 'titl', 'tnum'])
        fea = drawBot.openTypeFeatures(liga=False)
        self.assertEqual(fea, {'liga': False})
        drawBot.font("LucidaGrande")
        fea = drawBot.openTypeFeatures(resetFeatures=True)
        self.assertEqual(fea, {})

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
        var['wght'] = _roundDictValues(var['wght'], 3)
        var['wdth'] = _roundDictValues(var['wdth'], 3)
        expectedVar = OrderedDict({
            'wght': {'name': 'Weight', 'minValue': 0.48, 'maxValue': 3.2, 'defaultValue': 1.0},
            'wdth': {'name': 'Width', 'minValue': 0.62, 'maxValue': 1.3, 'defaultValue': 1.0},
        })
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

    def test_fontVariationNamedInstances(self):
        drawBot.newDrawing()
        namedInstances = drawBot.listNamedInstances()
        self.assertEqual(namedInstances, {})
        drawBot.font("Skia")
        namedInstances = drawBot.listNamedInstances()
        namedInstances = _roundInstanceLocations(namedInstances)
        expectedNamedInstances = {'Skia-Regular_Black': {'wght': 3.2, 'wdth': 1.0}, 'Skia-Regular_Extended': {'wght': 1.0, 'wdth': 1.3}, 'Skia-Regular_Condensed': {'wght': 1.0, 'wdth': 0.61998}, 'Skia-Regular_Light': {'wght': 0.48, 'wdth': 1.0}, 'Skia-Regular': {'wght': 1.0, 'wdth': 1.0}, 'Skia-Regular_Black-Extended': {'wght': 3.2, 'wdth': 1.3}, 'Skia-Regular_Light-Extended': {'wght': 0.48, 'wdth': 1.3}, 'Skia-Regular_Black-Condensed': {'wght': 3.0, 'wdth': 0.7}, 'Skia-Regular_Light-Condensed': {'wght': 0.48, 'wdth': 0.7}, 'Skia-Regular_Bold': {'wght': 1.95, 'wdth': 1.0}}
        expectedNamedInstances = _roundInstanceLocations(expectedNamedInstances)
        self.assertEqual(namedInstances, expectedNamedInstances)
        drawBot.font("Helvetica")
        namedInstances = drawBot.listNamedInstances("Skia")
        namedInstances = _roundInstanceLocations(namedInstances)
        self.assertEqual(namedInstances, expectedNamedInstances)

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
        out = io.StringIO()
        ScriptRunner("print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = io.StringIO()
        ScriptRunner("print(u'hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = io.StringIO()
        ScriptRunner(u"print('hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')
        out = io.StringIO()
        ScriptRunner(u"print(u'hey!')", stdout=out, stderr=out)
        self.assertEqual(out.getvalue(), u'hey!\n')

    def test_ScriptRunner_print_function(self):
        out = StdOutCollector()
        ScriptRunner("print 'hey!'", stdout=out, stderr=out)
        self.assertEqual(out.lines()[-1], "SyntaxError: Missing parentheses in call to 'print'. Did you mean print('hey!')?")

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
            self.assertEqual(out.lines(), ["0.5"])
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

    def test_font_install(self):
        fontPath = os.path.join(testDataDir, "MutatorSans.ttf")
        drawBot.newDrawing()
        drawBot.newPage()
        postscriptName = drawBot.font(fontPath)
        self.assertEqual(postscriptName, "MutatorMathTest-LightCondensed")
        variations = drawBot.listFontVariations()
        self.assertEqual(variations, {'wdth': {'name': 'Width', 'minValue': 0.0, 'maxValue': 1000.0, 'defaultValue': 0.0}, 'wght': {'name': 'Weight', 'minValue': 0.0, 'maxValue': 1000.0, 'defaultValue': 0.0}})

    def test_formattedString_issue337(self):
        # https://github.com/typemytype/drawbot/issues/337
        drawBot.newDrawing()
        fs = drawBot.FormattedString("A\n")
        drawBot.text(fs, (0, 0))

    def test_formattedString_issue337_part2(self):
        # https://github.com/typemytype/drawbot/issues/337
        drawBot.newDrawing()
        fs = drawBot.FormattedString("A\n\n")
        drawBot.text(fs, (0, 0))

    def test_formattedString_issue337_part3(self):
        # Verifying we get the correct line height on an empty string
        expected = [
            'reset None',
            'newPage 1000 1000',
            'textBox A 0 -34.0 26.8994140625 104.0 left',
            'textBox B 0 -48.0 25.751953125 104.0 left',
            'textBox C 0 -62.0 26.9189453125 104.0 left',
            'textBox A 10 -34.0 26.8994140625 104.0 left',
            'textBox C 10 -62.0 26.9189453125 104.0 left',
            "saveImage * {}",
        ]
        with StdOutCollector() as output:
            import drawBot
            drawBot.newDrawing()
            fs = drawBot.FormattedString("A\nB\nC\n")
            drawBot.text(fs, (0, 60))
            fs = drawBot.FormattedString("A\n\nC\n")
            drawBot.text(fs, (10, 60))
            drawBot.saveImage("*")
            drawBot.endDrawing()
        self.assertEqual(output.lines(), expected)


def _roundInstanceLocations(instanceLocations):
    return {instanceName: {tag: round(value, 3) for tag, value in location.items()} for instanceName, location in instanceLocations.items()}


if __name__ == '__main__':
    sys.exit(unittest.main())
