import sys
import os
import unittest

from testSupport import TempFile, readData, testDataDir

import drawBot
from drawBot.misc import DrawBotError
from drawBot.context.baseContext import BezierPath, FormattedString, ContextPropertyMixin, SVGContextPropertyMixin


class Dummy(SVGContextPropertyMixin, ContextPropertyMixin):

    def copy(self):
        new = self.__class__()
        new.copyContextProperties(self)
        return new


class SVGMixinTest(unittest.TestCase):

    def _svg_mixin(self, o, value):
        self.assertEqual(o.svgID, value)
        self.assertEqual(o.svgClass, value)
        self.assertEqual(o.svgLink, value)

    def _getObjects(self):
        return [
            Dummy(),
            BezierPath(),
            FormattedString()
        ]

    def test_empty_SVG_mixin(self):
        objs = self._getObjects()
        for obj in objs:
            self._svg_mixin(obj, None)

    def test_setting_SVG_mixin(self):
        objs = self._getObjects()
        for obj in objs:
            obj.svgID = "foo"
            obj.svgClass = "foo"
            obj.svgLink = "foo"
            self._svg_mixin(obj, "foo")

    def test_setting_SVG_mixin_notValid(self):
        objs = self._getObjects()
        for obj in objs:
            obj.svgID = None
            obj.svgClass = None
            obj.svgLink = None
            with self.assertRaises(DrawBotError) as cm:
                obj.svgID = list()
            self.assertEqual(cm.exception.args[0], "'svgID' must be a string.")
            with self.assertRaises(DrawBotError) as cm:
                obj.svgClass = dict()
            self.assertEqual(cm.exception.args[0], "'svgClass' must be a string.")
            with self.assertRaises(DrawBotError) as cm:
                obj.svgLink = set()
            self.assertEqual(cm.exception.args[0], "'svgLink' must be a string.")

    def test_deleting_SVG_mixin(self):
        objs = self._getObjects()
        for obj in objs:
            obj.svgID = "foo"
            obj.svgClass = "foo"
            obj.svgLink = "foo"
            self._svg_mixin(obj, "foo")
            del obj.svgID
            del obj.svgClass
            del obj.svgLink
            self._svg_mixin(obj, None)

    def test_copy_SVG_mixin(self):
        objs = self._getObjects()
        for obj in objs:
            new = obj.copy()
            self._svg_mixin(new, None)

            obj.svgID = "foo"
            obj.svgClass = "foo"
            obj.svgLink = "foo"

            new = obj.copy()
            self._svg_mixin(new, "foo")

            del obj.svgID
            del obj.svgClass
            del obj.svgLink

            new = obj.copy()
            self._svg_mixin(new, None)

    def test_export_SVG_mixin(self):
        expectedPath = os.path.join(testDataDir, "expected_svgMixin.svg")
        drawBot.newDrawing()
        drawBot.newPage(100, 100)
        path = drawBot.BezierPath()
        path.svgID = "hello"
        path.svgClass = "foo bar"
        path.svgLink = "drawbot.com"
        path.rect(0, 0, 20, 20)
        drawBot.drawPath(path)
        txt = drawBot.FormattedString()
        txt += "world"
        txt.svgID = "hello"
        txt.svgClass = "foo bar"
        txt.svgLink = "drawbot.com"
        drawBot.text(txt, (20, 20))

        with TempFile(suffix=".svg") as tmp:
            drawBot.saveImage(tmp.path)
            self.assertEqual(readData(tmp.path), readData(expectedPath), "Files %r and %s are not the same" % (tmp.path, expectedPath))


if __name__ == '__main__':
    sys.exit(unittest.main())
