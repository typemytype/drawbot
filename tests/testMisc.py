import sys
import os
import pathlib
import unittest
import io
import tempfile
from collections import OrderedDict
from fontTools.ttLib import TTFont
import drawBot
from drawBot.misc import DrawBotError, warnings, validateLanguageCode
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

    def test_listFontNamedInstances(self):
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

    def test_fontNamedInstance(self):
        drawBot.newDrawing()
        drawBot.font("Skia")
        drawBot.fontNamedInstance("Skia-Regular_Black-Extended")
        with self.assertRaises(DrawBotError) as cm:
            drawBot.fontNamedInstance("foo bar")
        self.assertEqual(cm.exception.args[0], "Can not find instance with name: 'foo bar' for 'Skia-Regular'.")

    def test_textProperties(self):
        drawBot.newDrawing()
        fs = drawBot.FormattedString()
        self.assertEqual(fs.textProperties(), fs._formattedAttributes)
        fs.font("Skia")
        self.assertEqual(fs.textProperties()["font"], "Skia")
        fs.fill(1, 0, 0)
        self.assertEqual(fs.textProperties()["fill"], (1, 0, 0))
        fs.openTypeFeatures(liga=True)
        self.assertEqual(fs.textProperties()["openTypeFeatures"], dict(liga=True))

        fs += "foo"
        fs.fill(0, 1, 0)
        fs += "bar"
        fs.fill(None)
        fs += "world"
        characterBounds = drawBot.textBoxCharacterBounds(fs, (0, 0, 1000, 1000))
        fillColors = []
        for characterBound in characterBounds:
            fillColors.append(characterBound.formattedSubString.textProperties()["fill"])
        self.assertEqual(fillColors, [(1, 0, 0), (0, 1, 0), None])

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

    def test_font_install_pathlib(self):
        import pathlib
        fontPath = os.path.join(testDataDir, "MutatorSans.ttf")
        fontPath = pathlib.Path(fontPath)
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
            'textBox B 0 -46.0 25.751953125 104.0 left',
            'textBox C 0 -58.0 26.9189453125 104.0 left',
            'textBox A 10 -34.0 26.8994140625 104.0 left',
            'textBox  10 48.0 20.0 104.0 left',
            'textBox C 10 -58.0 26.9189453125 104.0 left',
            'saveImage * {}'
        ]
        with StdOutCollector() as output:
            drawBot.newDrawing()
            fs = drawBot.FormattedString("A\nB\nC\n")
            drawBot.text(fs, (0, 60))
            fs = drawBot.FormattedString("A\n\nC\n")
            drawBot.text(fs, (10, 60))
            drawBot.saveImage("*")
            drawBot.endDrawing()
        self.assertEqual(output.lines(), expected)

    def test_textBoxBaselines(self):
        drawBot.newDrawing()
        baselines = drawBot.textBoxBaselines("hello foo bar world " * 10, (10, 10, 300, 300))
        self.assertEqual(baselines, [(10.0, 300.0), (10.0, 288.0), (10.0, 276.0), (10.0, 264.0)])

        t = drawBot.FormattedString()
        t += "hello " * 2
        t.fontSize(30)
        t += "foo " * 2
        t.font("Times")
        t += "bar " * 2
        t.fontSize(40)
        t += "world " * 2
        baselines = drawBot.textBoxBaselines(t, (10, 10, 300, 300))
        self.assertEqual(baselines, [(10.0, 281.0), (10.0, 235.0)])

    def test_textBoxCharacterBounds(self):
        drawBot.newDrawing()
        t = drawBot.FormattedString()
        t += "hello " * 2
        t.fontSize(30)
        t += "foo " * 2
        t.font("Times")
        t += "bar " * 2
        t.fontSize(40)
        t += "world " * 2
        bounds = drawBot.textBoxCharacterBounds(t, (10, 10, 300, 300))
        self.assertEqual([i.bounds for i in bounds], [(10.0, 278.890625, 53.73046875, 11.77734375), (63.73046875, 274.671875, 114.755859375, 35.33203125), (178.486328125, 273.5, 91.611328125, 30.0), (10.0, 225.0, 206.640625, 40.0)])
        self.assertEqual([i.baselineOffset for i in bounds], [2.109375, 6.328125, 7.5, 10.0])
        self.assertEqual([str(i.formattedSubString) for i in bounds], ['hello hello ', 'foo foo ', 'bar bar ', 'world world '])

    def test_reloadFont(self):
        src = pathlib.Path(__file__).resolve().parent / "data" / "MutatorSans.ttf"
        assert src.exists()
        with tempfile.NamedTemporaryFile(suffix=".ttf") as ff:
            ff.write(src.read_bytes())
            firstModTime = os.stat(ff.name).st_mtime
            drawBot.newDrawing()
            drawBot.font(ff.name)
            self.assertEqual(ff.name, drawBot.fontFilePath())
            path = drawBot.BezierPath()
            path.text("E", font=ff.name, fontSize=1000)
            self.assertEqual((60.0, 0.0, 340.0, 700.0), path.bounds())
            ff.seek(0)
            ttf = TTFont(ff)
            ttf["glyf"]["E"].coordinates[0] = (400, 800)
            ff.seek(0)
            ttf.save(ff)
            secondModTime = os.stat(ff.name).st_mtime
            assert firstModTime != secondModTime, (firstModTime, secondModTime)
            drawBot.newDrawing()  # to clear the memoize cache in baseContext
            drawBot.font(ff.name)
            self.assertEqual(ff.name, drawBot.fontFilePath())
            path = drawBot.BezierPath()
            path.text("E", font=ff.name, fontSize=1000)
            self.assertEqual((60.0, 0.0, 400.0, 800.0), path.bounds())

    def test_ttc_IndexError(self):
        src = pathlib.Path(__file__).resolve().parent / "data" / "MutatorSans.ttc"
        self.assertEqual("MutatorMathTest-LightCondensed", drawBot.font(src, fontNumber=0))
        self.assertEqual("MutatorMathTest-LightWide", drawBot.font(src, fontNumber=1))
        self.assertEqual("MutatorMathTest-BoldCondensed", drawBot.font(src, fontNumber=2))
        self.assertEqual("MutatorMathTest-BoldWide", drawBot.font(src, fontNumber=3))
        with self.assertRaises(IndexError):
            drawBot.font(src, fontNumber=4)
        with self.assertRaises(IndexError):
            drawBot.font(src, fontNumber=-1)

    def test_norm(self):
        assert drawBot.norm(20, 10, 30) == 0.5
        assert drawBot.norm(-10, 10, 30) == -1
        with self.assertRaises(ZeroDivisionError):
            drawBot.norm(20, 10, 10)

    def test_lerp(self):
        assert drawBot.lerp(10, 30, 0.5) == 20
        assert drawBot.lerp(10, 10, 0.5) == 10
        assert drawBot.lerp(10, 30, 0) == 10
        assert drawBot.lerp(10, 30, 1) == 30
        assert drawBot.lerp(10, 30, 2) == 50

    def test_remap(self):
        assert drawBot.remap(15, 10, 20, 30, 50) == 40
        with self.assertRaises(ZeroDivisionError):
            drawBot.remap(15, 20, 20, 30, 50)
        assert drawBot.remap(5, 10, 20, 30, 50) == 20
        assert drawBot.remap(5, 10, 20, 30, 50, clamp=True) == 30
        assert drawBot.remap(25, 10, 20, 30, 50) == 60
        assert drawBot.remap(25, 10, 20, 30, 50, clamp=True) == 50

    def test_validateLanguageCode(self):
        expectedLanguageValidation = [
            ("ab", False),
            ("abk", False),
            ("abz", False),
            ("AB", False),
            ("af", True),
            ("afr", True),
            ("af_NA", True),
            ("afr_NA", True),
            ("af_ZZ", False),
            ("afr_ZZ", False),
            ("en-us", True),
            ("en_us", True),
            ("EN-US", True),
            ("en-zz", False),
            ("sr_Cyrl_ME", True),
            ("en", True),
        ]
        for language, expectedValue in expectedLanguageValidation:
            assert validateLanguageCode(language) == expectedValue

            with StdOutCollector(captureStdErr=True) as output:
                drawBot.language(language)
            if expectedValue:
                assert output.lines() == []
            else:
                assert output.lines() == [f"*** DrawBot warning: Language '{language}' is not available. ***"]


def _roundInstanceLocations(instanceLocations):
    return {instanceName: {tag: round(value, 3) for tag, value in location.items()} for instanceName, location in instanceLocations.items()}


if __name__ == '__main__':
    sys.exit(unittest.main())
