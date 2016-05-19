import AppKit
import CoreText
import Quartz

import math
import os
import random

from context import getContextForFileExt
from context.baseContext import BezierPath, FormattedString
from context.dummyContext import DummyContext

from context.tools import openType
from context.tools.imageObject import ImageObject

from misc import DrawBotError, warnings, VariableController, optimizePath, isPDF, isEPS


def _getmodulecontents(module, names=None):
    d = {}
    if names is None:
        names = [name for name in dir(module) if not name.startswith("_")]
    for name in names:
        d[name] = getattr(module, name)
    return d


def _deprecatedWarningLowercase(txt):
    warnings.warn("lowercase API is deprecated use: '%s'" % txt)


def _deprecatedWarningWrapInTuple(txt):
    warnings.warn("deprecated syntax, wrap x and y values in a tuple: '%s'" % txt)

_chachedPixelColorBitmaps = {}

_paperSizes = {
    'Letter'      : (612, 792),
    'LetterSmall' : (612, 792),
    'Tabloid'     : (792, 1224),
    'Ledger'      : (1224, 792),
    'Legal'       : (612, 1008),
    'Statement'   : (396, 612),
    'Executive'   : (540, 720),
    'A0'          : (2384, 3371),
    'A1'          : (1685, 2384),
    'A2'          : (1190, 1684),
    'A3'          : (842, 1190),
    'A4'          : (595, 842),
    'A4Small'     : (595, 842),
    'A5'          : (420, 595),
    'B4'          : (729, 1032),
    'B5'          : (516, 729),
    'Folio'       : (612, 936),
    'Quarto'      : (610, 780),
    '10x14'       : (720, 1008),
}

for key, (w, h) in _paperSizes.items():
    _paperSizes["%sLandscape" % key] = (h, w)


class DrawBotDrawingTool(object):

    def __init__(self):
        self._reset()

    def _get__all__(self):
        return [i for i in dir(self) if not i.startswith("_")] + ["__version__"]

    __all__ = property(_get__all__)

    def _get_version(self):
        try:
            import drawBotSettings
            return drawBotSettings.__version__
        except:
            # DrawBot is installed as a module
            import pkg_resources
            return pkg_resources.require("drawBot")[0].version
        return ""

    __version__ = property(_get_version)

    def _addToNamespace(self, namespace):
        namespace.update(_getmodulecontents(self, self.__all__))
        namespace.update(_getmodulecontents(random, ["random", "randint", "choice"]))
        namespace.update(_getmodulecontents(math))

    def _addInstruction(self, callback, *args, **kwargs):
        if self._requiresNewFirstPage and not self._hasPage:
            self._hasPage = True
            self._instructionsStack.append(("newPage", [self.width(), self.height()], {}))
        self._instructionsStack.append((callback, args, kwargs))

    def _drawInContext(self, context):
        if not self._instructionsStack:
            return
        for callback, args, kwargs in self._instructionsStack:
            attr = getattr(context, callback)
            attr(*args, **kwargs)

    def _reset(self, other=None):
        if other is not None:
            self._instructionsStack = list(other._instructionsStack)
            self._dummyContext = other._dummyContext
            self._width = other._width
            self._height = other._height
            self._tempInstalledFonts = dict(other._tempInstalledFonts)
            self._requiresNewFirstPage = other._requiresNewFirstPage
            self._hasPage = other._hasPage
        else:
            self._instructionsStack = []
            self._dummyContext = DummyContext()
            self._width = None
            self._height = None
            self._requiresNewFirstPage = False
            self._hasPage = False
            if not hasattr(self, "_tempInstalledFonts"):
                self._tempInstalledFonts = dict()

    def _copy(self):
        new = self.__class__()
        new._instructionsStack = list(self._instructionsStack)
        new._dummyContext = self._dummyContext
        new._width = self._width
        new._height = self._height
        new._tempInstalledFonts = dict(self._tempInstalledFonts)
        return new

    def newDrawing(self):
        """
        Reset the drawing stack to the clean and empty stack.

        .. showcode:: /../examples/newDrawing.py
        """
        self._reset()
        self.installedFonts()

    def endDrawing(self):
        """
        Explicitly tell drawBot the drawing is done.
        This is advised when using drawBot as a standalone module.
        """
        self._uninstallAllFonts()

    # magic variables

    def width(self):
        """
        Returns the width of the current page.
        """
        if self._width is None:
            return 1000
        return self._width

    def _get_width(self):
        warnings.warn("Magic variables are deprecated.'")
        return self.width()

    WIDTH = property(_get_width)

    def height(self):
        """
        Returns the height of the current page.
        """
        if self._height is None:
            return 1000
        return self._height

    def _get_height(self):
        warnings.warn("Magic variables are deprecated.'")
        return self.height()

    HEIGHT = property(_get_height)

    def sizes(self, paperSize=None):
        """
        Returns the width and height of a specified canvas size.
        If no canvas size is given it will return the dictionary containing all possible page sizes.
        """
        _paperSizes["screen"] = tuple(AppKit.NSScreen.mainScreen().frame().size)
        if paperSize:
            return _paperSizes[paperSize]
        return _paperSizes

    def pageCount(self):
        """
        Returns the current page count.
        """
        pageCount = 0
        for i in self._instructionsStack:
            if i[0] == "newPage":
                pageCount += 1
        return pageCount

    def _get_pageCount(self):
        warnings.warn("Magic variables are deprecated.'")
        return self.pageCount()

    PAGECOUNT = property(_get_pageCount)

    _magicVariables = ["WIDTH", "HEIGHT", "PAGECOUNT"]

    # ====================
    # = public callbacks =
    # ====================

    # size and pages

    def size(self, width, height=None):
        """
        Set the width and height of the canvas.
        Without calling `size()` the default drawing board is 1000 by 1000 points.

        Alternatively `size('A4')` with a supported papersizes or `size('screen')` setting the current screen size as size, can be used.

        Afterwards the functions `width()` and `height()` can be used for calculations.

        It is advised to use `size()` always at the top of the script and not use `size()`
        in a multiple page document use `newPage(w, h)` to set the correct dimentions directly.

        .. showcode:: /../examples/size.py

        All supported papersizes: 10x14, 10x14Landscape, A0, A0Landscape, A1, A1Landscape, A2, A2Landscape, A3, A3Landscape, A4, A4Landscape, A4Small, A4SmallLandscape, A5, A5Landscape, B4, B4Landscape, B5, B5Landscape, Executive, ExecutiveLandscape, Folio, FolioLandscape, Ledger, LedgerLandscape, Legal, LegalLandscape, Letter, LetterLandscape, LetterSmall, LetterSmallLandscape, Quarto, QuartoLandscape, Statement, StatementLandscape, Tabloid, TabloidLandscape.
        """
        if width in _paperSizes:
            width, height = _paperSizes[width]
        if width == "screen":
            width, height = AppKit.NSScreen.mainScreen().frame().size
        if height is None:
            width, height = width
        self._width = width
        self._height = height
        if not self._instructionsStack:
            self.newPage(width, height)
        else:
            raise DrawBotError("It is advised to use 'size()' at the top of a script.")

    def newPage(self, width=None, height=None):
        """
        Create a new canvas to draw in.
        This will act like a page in a pdf or a frame in a mov.

        Optionally a `width` and `height` argument can be provided to set the size.
        If not provided the default size will be used.

        Alternatively `size('A4')` with a supported papersizes or `size('screen')` setting the current screen size as size, can be used.

        .. showcode:: /../examples/newPage.py

        All supported papersizes: 10x14, 10x14Landscape, A0, A0Landscape, A1, A1Landscape, A2, A2Landscape, A3, A3Landscape, A4, A4Landscape, A4Small, A4SmallLandscape, A5, A5Landscape, B4, B4Landscape, B5, B5Landscape, Executive, ExecutiveLandscape, Folio, FolioLandscape, Ledger, LedgerLandscape, Legal, LegalLandscape, Letter, LetterLandscape, LetterSmall, LetterSmallLandscape, Quarto, QuartoLandscape, Statement, StatementLandscape, Tabloid, TabloidLandscape.
        """
        if width in _paperSizes:
            width, height = _paperSizes[width]
        if width == "screen":
            width, height = AppKit.NSScreen.mainScreen().frame().size
        self._width = width
        self._height = height
        self._hasPage = True
        self._addInstruction("newPage", width, height)

    def newpage(self, width=None, height=None):
        _deprecatedWarningLowercase("newPage(%s, %s)" % (width, height))
        self.newPage(width, height)

    def saveImage(self, paths, multipage=None):
        """
        Save or export the canvas to a specified format.
        The argument `paths` can either be a single path or a list of paths.

        The file extension is important because it will determine the format in which the image will be exported.

        All supported file extensions: `pdf`, `svg`, `png`, `jpg`, `jpeg`, `tiff`, `tif`, `gif`, `bmp` and `mov`.

        * A `pdf` can be multipage. If `multipage` is `False` only the current page is saved.
        * A `mov` will use each page as a frame.
        * A `gif` can be animated when there are multiple pages and it will use each page as a frame.
        * All images and `svg` formats will only save the current page. If `multipage` is `True` all pages are saved to disk (a page index will be added to the file name).

        .. showcode:: /../examples/saveImage.py
        """
        if isinstance(paths, (str, unicode)):
            paths = [paths]
        for rawPath in paths:
            path = optimizePath(rawPath)
            dirName = os.path.dirname(path)
            if not os.path.exists(dirName):
                raise DrawBotError("Folder '%s' doesn't exists" % dirName)
            base, ext = os.path.splitext(path)
            ext = ext.lower()[1:]
            if not ext:
                ext = rawPath
            context = getContextForFileExt(ext)
            if context is None:
                raise DrawBotError("Did not found a supported context for: '%s'" % ext)
            self._drawInContext(context)
            context.saveImage(path, multipage)

    def saveimage(self, paths):
        _deprecatedWarningLowercase("saveImage()")
        self.saveImage(paths)

    def printImage(self, pdf=None):
        """
        Export the canvas to a printing dialog, ready to print.

        Optionally a `pdf` object can be provided.

        .. showcode:: /../examples/printImage.py
        """
        context = getContextForFileExt("pdf")
        if pdf is None:
            self._drawInContext(context)
            context.printImage()
        else:
            context.printImage(pdf)

    def pdfImage(self):
        """
        Return the image as a pdf document object.
        """
        from context.drawBotContext import DrawBotContext
        context = DrawBotContext()
        self._drawInContext(context)
        return context.getNSPDFDocument()

    # graphic state

    def save(self):
        """
        Save the current state.
        This will save the state of the canvas (with all the transformations)
        but also the state of the colors, strokes...
        """
        self._dummyContext.save()
        self._requiresNewFirstPage = True
        self._addInstruction("save")

    def restore(self):
        """
        Restore from a previously saved state.
        This will restore the state of the canvas (with all the transformations)
        but also the state of colors, strokes...
        """
        self._dummyContext.restore()
        self._requiresNewFirstPage = True
        self._addInstruction("restore")

    # basic shapes

    def rect(self, x, y, w, h):
        """
        Draw a rectangle from position x, y with the given width and height.

        .. showcode:: /../examples/rect.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("rect", x, y, w, h)

    def oval(self, x, y, w, h):
        """
        Draw an oval from position x, y with the given width and height.

        .. showcode:: /../examples/oval.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("oval", x, y, w, h)

    # path

    def newPath(self):
        """
        Create a new path.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("newPath")

    def newpath(self):
        _deprecatedWarningLowercase("newPath()")
        self.newPath()

    def moveTo(self, (x, y)):
        """
        Move to a point `x`, `y`.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("moveTo", (x, y))

    def moveto(self, x, y):
        _deprecatedWarningLowercase("moveTo((%s, %s))" % (x, y))
        self.moveTo((x, y))

    def lineTo(self, (x, y)):
        """
        Line to a point `x`, `y`.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("lineTo", (x, y))

    def lineto(self, x, y):
        _deprecatedWarningLowercase("lineTo((%s, %s))" % (x, y))
        self.lineTo((x, y))

    def curveTo(self, (x1, y1), (x2, y2), (x3, y3)):
        """
        Curve to a point `x3`, `y3`.
        With given bezier handles `x1`, `y1` and `x2`, `y2`.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("curveTo", (x1, y1), (x2, y2), (x3, y3))

    def curveto(self, x1, y1, x2, y2, x3, y3):
        _deprecatedWarningLowercase("curveTo((%s, %s), (%s, %s), (%s, %s))" % (x1, y1, x2, y2, x3, y3))
        self.curveTo((x1, y1), (x2, y2), (x3, y3))

    def arc(self, center, radius, startAngle, endAngle, clockwise):
        """
        Arc with `center` and a given `radius`, from `startAngle` to `endAngle`, going clockwise if `clockwise` is True and counter clockwise if `clockwise` is False.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("arc", center, radius, startAngle, endAngle, clockwise)

    def arcTo(self, (x1, y1), (x2, y2), radius):
        """
        Arc from one point to an other point with a given `radius`.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("arcTo", (x1, y1), (x2, y2), radius)

    def closePath(self):
        """
        Close the path.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("closePath")

    def closepath(self):
        _deprecatedWarningLowercase("closePath()")
        self.closePath()

    def drawPath(self, path=None):
        """
        Draw the current path, or draw the provided path.
        """
        if isinstance(path, AppKit.NSBezierPath):
            path = self._bezierPathClass(path)
        if isinstance(path, self._bezierPathClass):
            path = path.copy()
        self._requiresNewFirstPage = True
        self._addInstruction("drawPath", path)

    def drawpath(self, path=None):
        warning = "drawPath()"
        if path:
            warning = "drawPath(pathObject)"
        _deprecatedWarningLowercase(warning)
        self.drawPath(path)

    def clipPath(self, path=None):
        """
        Use the current path as a clipping path.
        The clipping path will be used until the canvas gets a `restore()`.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("clipPath", path)

    def clippath(self, path=None):
        _deprecatedWarningLowercase("clipPath(path)")
        self.clipPath(path)

    def line(self, x1, y1, x2=None, y2=None):
        """
        Draws a line between two given points.

        .. showcode:: /../examples/line.py
        """
        if x2 is None and y2 is None:
            (x1, y1), (x2, y2) = x1, y1
        else:
            _deprecatedWarningWrapInTuple("line((%s, %s), (%s, %s))" % (x1, y1, x2, y2))
        path = self._bezierPathClass()
        path.moveTo((x1, y1))
        path.lineTo((x2, y2))
        self.drawPath(path)

    def polygon(self, x, y=None, *args, **kwargs):
        """
        Draws a polygon with n-amount of points.
        Optionally a `close` argument can be provided to open or close the path.
        As default a `polygon` is a closed path.

        .. showcode:: /../examples/polygon.py
        """
        try:
            a, b = x
        except TypeError:
            args = [args[i:i+2] for i in range(0, len(args), 2)]
            _deprecatedWarningWrapInTuple("polygon((%s, %s), %s)" % (x, y, ", ".join([str(i) for i in args])))
        else:
            args = list(args)
            args.insert(0, y)
            x, y = x
        if not args:
            raise DrawBotError("polygon() expects more than a single point")
        doClose = kwargs.get("close", True)
        if len(kwargs) > 1:
            raise DrawBotError("unexpected keyword argument for this function")

        path = self._bezierPathClass()
        path.moveTo((x, y))
        for x, y in args:
            path.lineTo((x, y))
        if doClose:
            path.closePath()
        self.drawPath(path)

    # color

    def colorSpace(self, colorSpace):
        """
        Set the color space.
        Options are `genericRGB`, `adobeRGB1998`, `sRGB`, `genericGray`, `genericGamma22Gray`.
        The default is `genericRGB`.
        `None` will reset it back to the default.

        .. showCode:: /../examples/colorSpace.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("colorSpace", colorSpace)

    def listColorSpaces(self):
        """
        Return a list of all available color spaces.
        """
        return self._dummyContext._colorSpaceMap.keys()

    def blendMode(self, operation):
        """
        Set a blend mode.

        Available operations are: `normal`, `multiply`, `screen`, `overlay`,
        `darken`, `lighten`, `colorDodge`, `colorBurn`, `softLight`,
        `hardLight`, `difference`, `exclusion`, `hue`, `saturation`,
        `color`, `luminosity`, `clear`, `copy`, `sourceIn`, `sourceOut`,
        `sourceAtop`, `destinationOver`, `destinationIn`, `destinationOut`,
        `destinationAtop`, `xOR`, `plusDarker` and `plusLighter`,

        .. showcode:: /../examples/blendMode.py
        """
        if operation not in self._dummyContext._blendModeMap.keys():
            raise DrawBotError("blend mode must be %s" % (", ".join(self._dummyContext._blendModeMap.keys())))
        self._requiresNewFirstPage = True
        self._addInstruction("blendMode", operation)

    def fill(self, r=None, g=None, b=None, alpha=1):
        """
        Sets the fill color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.

        .. showcode:: /../examples/fill.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("fill", r, g, b, alpha)

    def stroke(self, r=None, g=None, b=None, alpha=1):
        """
        Sets the stroke color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.

        .. showcode:: /../examples/stroke.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("stroke", r, g, b, alpha)

    def cmykFill(self, c, m=None, y=None, k=None, alpha=1):
        """
        Set a fill using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK fill color. Each value must be a float between 0.0 and 1.0.

        .. showcode:: /../examples/cmykFill.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("cmykFill", c, m, y, k, alpha)

    def cmykfill(self, c,  m=None, y=None, k=None, alpha=1):
        _deprecatedWarningLowercase("cmykFill(%s, %s, %s, %s, alpha=%s)" % (c, m, y, k, alpha))
        self.cmykFill(c, m, y, k)

    def cmykStroke(self, c, m=None, y=None, k=None, alpha=1):
        """
        Set a stroke using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK stroke color. Each value must be a float between 0.0 and 1.0.

        .. showcode:: /../examples/cmykStroke.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("cmykStroke", c, m, y, k, alpha)

    def cmykstroke(self, c,  m=None, y=None, k=None, alpha=1):
        _deprecatedWarningLowercase("cmykStroke(%s, %s, %s, %s, alpha=%s)" % (c, m, y, k, alpha))
        self.cmykStroke(c, m, y, k)

    def shadow(self, offset, blur=None, color=None):
        """
        Adds a shadow with an `offset` (x, y), `blur` and a `color`.
        The `color` argument must be a tuple similarly as `fill`.
        The `offset`and `blur` argument will be drawn indepeneded of the current
        context transformations.

        .. showcode:: /../examples/shadow.py
        """
        if color is None:
            color = (0, 0, 0)
        if blur is None:
            blur = 10
        self._requiresNewFirstPage = True
        self._addInstruction("shadow", offset, blur, color)

    def cmykShadow(self, offset, blur=None, color=None):
        """
        Adds a cmyk shadow with an `offset` (x, y), `blur` and a `color`.
        The `color` argument must be a tuple similarly as `cmykFill`.

        .. showcode:: /../examples/cmykShadow.py
        """
        if color is None:
            color = (0, 0, 0, 1, 1)
        if blur is None:
            blur = 10
        self._requiresNewFirstPage = True
        self._addInstruction("cmykShadow", offset, blur, color)

    def cmykshadow(self, offset, blur=None, color=None):
        _deprecatedWarningLowercase("cmykShadow(%s,  %s, %s)" % (offset, blur, color))
        self.cmykShadow(offset, blur, color)

    def linearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        """
        A linear gradient fill with:

        * `startPoint` as (x, y)
        * `endPoint` as (x, y)
        * `colors` as a list of colors, described similary as `fill`
        * `locations` of each color as a list of floats. (optionally)

        Setting a gradient will ignore the `fill`.

        .. showcode:: /../examples/linearGradient.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("linearGradient", startPoint, endPoint, colors, locations)

    def lineargradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        _deprecatedWarningLowercase("linearGradient(%s,  %s, %s, %s)" % (startPoint, endPoint, colors, locations))
        self.linearGradient(startPoint, endPoint, colors, locations)

    def cmykLinearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        """
        A cmyk linear gradient fill with:

        * `startPoint` as (x, y)
        * `endPoint` as (x, y)
        * `colors` as a list of colors, described similary as `cmykFill`
        * `locations` of each color as a list of floats. (optionally)

        Setting a gradient will ignore the `fill`.

        .. showcode:: /../examples/cmykLinearGradient.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("cmykLinearGradient", startPoint, endPoint, colors, locations)

    def cmyklinearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        _deprecatedWarningLowercase("cmykLinearGradient(%s,  %s, %s, %s)" % (startPoint, endPoint, colors, locations))
        self.cmykLinearGradient(startPoint, endPoint, colors, locations)

    def radialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        """
        A radial gradient fill with:

        * `startPoint` as (x, y)
        * `endPoint` as (x, y)
        * `colors` as a list of colors, described similary as `fill`
        * `locations` of each color as a list of floats. (optionally)
        * `startRadius` radius around the startPoint in degrees (optionally)
        * `endRadius` radius around the endPoint in degrees (optionally)

        Setting a gradient will ignore the `fill`.

        .. showcode:: /../examples/radialGradient.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("radialGradient", startPoint, endPoint, colors, locations, startRadius, endRadius)

    def radialgradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        _deprecatedWarningLowercase("radialGradient(%s,  %s, %s, %s, %s, %s)" % (startPoint, endPoint, colors, locations, startRadius, endRadius))
        self.radialGradient(startPoint, endPoint, colors, locations, startRadius, endRadius)

    def cmykRadialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        """
        A cmyk radial gradient fill with:

        * `startPoint` as (x, y)
        * `endPoint` as (x, y)
        * `colors` as a list of colors, described similary as `cmykFill`
        * `locations` of each color as a list of floats. (optionally)
        * `startRadius` radius around the startPoint in degrees (optionally)
        * `endRadius` radius around the endPoint in degrees (optionally)

        Setting a gradient will ignore the `fill`.

        .. showcode:: /../examples/cmykRadialGradient.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("cmykRadialGradient", startPoint, endPoint, colors, locations, startRadius, endRadius)

    def cmykradialgradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        _deprecatedWarningLowercase("cmykRadialGradient(%s,  %s, %s, %s, %s, %s)" % (startPoint, endPoint, colors, locations, startRadius, endRadius))
        self.cmykRadialGradient(startPoint, endPoint, colors, locations, startRadius, endRadius)

    # path drawing behavoir

    def strokeWidth(self, value):
        """
        Sets stroke width.

        .. showcode:: /../examples/strokeWidth.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("strokeWidth", value)

    def strokewidth(self, value):
        _deprecatedWarningLowercase("strokeWidth(%s)" % value)
        self.strokeWidth(value)

    def miterLimit(self, value):
        """
        Set a miter limit. Used on corner points.

        .. showcode:: /../examples/miterLimit.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("miterLimit", value)

    def miterlimit(self, value):
        _deprecatedWarningLowercase("miterLimit(%s)" % value)
        self.miterLimit(value)

    def lineJoin(self, value):
        """
        Set a line join.

        Possible values are `miter`, `round` and `bevel`.

        .. showcode:: /../examples/lineJoin.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("lineJoin", value)

    def linejoin(self, value):
        _deprecatedWarningLowercase("lineJoin(%s)" % value)
        self.lineJoin(value)

    def lineCap(self, value):
        """
        Set a line cap.

        Possible values are `butt`, `square` and `round`.

        .. showcode:: /../examples/lineCap.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("lineCap", value)

    def linecap(self, value):
        _deprecatedWarningLowercase("lineCap(%s)" % value)
        self.lineCap(value)

    def lineDash(self, *value):
        """
        Set a line dash with any given amount of lenghts.
        Uneven lenghts will have a visible stroke, even lenghts will be invisible.

        .. showcode:: /../examples/lineDash.py
        """
        if not value:
            raise DrawBotError("lineDash must be a list of dashes or None")
        if isinstance(value[0], (list, tuple)):
            value = value[0]
        self._requiresNewFirstPage = True
        self._addInstruction("lineDash", value)

    def linedash(self, *value):
        _deprecatedWarningLowercase("lineDash(%s)" % ", ".join([str(i) for i in value]))
        self.lineDash(*value)

    # transform

    def transform(self, matrix):
        """
        Transform the canvas with a transformation matrix.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("transform", matrix)

    def translate(self, x=0, y=0):
        """
        Translate the canvas with a given offset.
        """
        self.transform((1, 0, 0, 1, x, y))

    def rotate(self, angle):
        """
        Rotate the canvas around the origin point with a given angle in degrees.
        """
        angle = math.radians(angle)
        c = math.cos(angle)
        s = math.sin(angle)
        self.transform((c, s, -s, c, 0, 0))

    def scale(self, x=1, y=None):
        """
        Scale the canvas with a given `x` (horizontal scale) and `y` (vertical scale).

        If only 1 argument is provided a proportional scale is applied.
        """
        if y is None:
            y = x
        self.transform((x, 0, 0, y, 0, 0))

    def skew(self, angle1, angle2=0):
        """
        Skew the canvas with given `angle1` and `angle2`.

        If only one argument is provided a proportional skew is applied.
        """
        angle1 = math.radians(angle1)
        angle2 = math.radians(angle2)
        self.transform((1, math.tan(angle2), math.tan(angle1), 1, 0, 0))

    # text

    def font(self, fontName, fontSize=None):
        """
        Set a font with the name of the font.
        If a font path is given the font will be installed and used directly.
        Optionally a `fontSize` can be set directly.
        The default font, also used as fallback font, is 'LucidaGrande'.
        The default `fontSize` is 10pt.

        The name of the font relates to the font's postscript name.

        ::

            font("Times-Italic")
        """
        fontName = self._tryInstallFontFromFontName(fontName)
        fontName = fontName.encode("ascii", "ignore")
        self._dummyContext.font(fontName, fontSize)
        self._addInstruction("font", fontName, fontSize)

    def fallbackFont(self, fontName):
        """
        Set a fallback font, this is used whenever a glyph is not available in the current font.

        ::

            fallbackFont("Times")
        """
        fontName = fontName.encode("ascii", "ignore")
        dummyFont = AppKit.NSFont.fontWithName_size_(fontName, 10)
        if dummyFont is None:
            raise DrawBotError("Fallback font '%s' is not available" % fontName)
        self._dummyContext.fallbackFont(fontName)
        self._addInstruction("fallbackFont", fontName)

    def fontSize(self, fontSize):
        """
        Set the font size in points.
        The default `fontSize` is 10pt.

        ::

            fontSize(30)
        """
        self._dummyContext.fontSize(fontSize)
        self._addInstruction("fontSize", fontSize)

    def fontsize(self, fontSize):
        _deprecatedWarningLowercase("fontSize(%s)" % fontSize)
        self.fontSize(fontSize)

    def lineHeight(self, value):
        """
        Set the line height.

        .. showcode:: /../examples/lineHeight.py
        """
        self._dummyContext.lineHeight(value)
        self._addInstruction("lineHeight", value)

    def lineheight(self, value):
        _deprecatedWarningLowercase("lineHeight(%s)" % value)
        self.lineHeight(value)

    def tracking(self, value):
        """
        Set the tracking between characters.

        .. showcode:: /../examples/tracking.py
        """
        self._dummyContext.tracking(value)
        self._addInstruction("tracking", value)

    def baselineShift(self, value):
        """
        Set the shift of the baseline.
        """
        self._dummyContext.baselineShift(value)
        self._addInstruction("baselineShift", value)

    def hyphenation(self, value):
        """
        Set hyphenation, `True` or `False`.

        .. showcode:: /../examples/hyphenation.py
        """
        self._dummyContext.hyphenation(value)
        self._addInstruction("hyphenation", value)

    def tabs(self, *tabs):
        """
        Set tabs, tuples of (`float`, `alignment`)
        Aligment can be `"left"`, `"center"`, `"right"` or any other character.
        If a character is provided the alignment will be `right` and centered on the specified character.

        .. showcode:: /../examples/tabs.py
        """
        if tabs and tabs[0] is None:
            self._dummyContext.tabs(None)
            self._addInstruction("tabs", None)
            return
        self._dummyContext.tabs(*tabs)
        self._addInstruction("tabs", *tabs)

    def openTypeFeatures(self, *args, **features):
        """
        Enable OpenType features.

        Supported OpenType tags:

        ::

            c2pc, c2sc, calt, case, cpsp, cswh, dlig, frac, liga, lnum, onum, ordn, pnum, rlig, sinf, smcp, ss01, ss02, ss03, ss04, ss05, ss06, ss07, ss08, ss09, ss10, ss11, ss12, ss13, ss14, ss15, ss16, ss17, ss18, ss19, ss20, subs, sups, swsh, titl, tnum

        .. showcode:: /../examples/openTypeFeatures.py
        """
        self._dummyContext.openTypeFeatures(*args, **features)
        self._addInstruction("openTypeFeatures", *args, **features)

    def listOpenTypeFeatures(self, fontName=None):
        """
        List all OpenType feature tags for the current font.

        Optionally a `fontName` can be given. If a font path is given the font will be installed and used directly.
        """
        if fontName:
            fontName = self._tryInstallFontFromFontName(fontName)
        else:
            fontName = self._dummyContext._state.text.fontName
        return openType.getFeatureTagsForFontName(fontName)

    # drawing text

    def text(self, txt, x, y=None):
        """
        Draw a text at a provided position.

        .. showcode:: /../examples/text.py
        """
        if isinstance(txt, (str, unicode)):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        if y is None:
            x, y = x
        else:
            warnings.warn("position must a tuple: text('%s', (%s, %s))" % (txt, x, y))
        attrString = self._dummyContext.attributedString(txt)
        w, h = attrString.size()
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = Quartz.CGPathCreateMutable()
        Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w*2, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CoreText.CTFrameGetLines(box)
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        if origins:
            x -= origins[-1][0]
            y -= origins[-1][1]
        self.textBox(txt, (x, y-h, w*2, h*2))

    def textBox(self, txt, (x, y, w, h), align=None):
        """
        Draw a text in a provided rectangle.
        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"`, `"right"` and `"justified"`.

        If the text overflows the rectangle, the overflowed text is returned.

        The default alignment is `left`.

        .. showcode:: /../examples/textBox.py
        """
        if isinstance(txt, (str, unicode)):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        if align is None:
            align = "left"
        elif align not in self._dummyContext._textAlignMap.keys():
            raise DrawBotError("align must be %s" % (", ".join(self._dummyContext._textAlignMap.keys())))
        self._requiresNewFirstPage = True
        self._addInstruction("textBox", txt, (x, y, w, h), align)
        return self._dummyContext.clippedText(txt, (x, y, w, h), align)

    def textbox(self, txt, x, y, w, h, align=None):
        _deprecatedWarningLowercase("textbox(%s, (%s, %s, %s, %s), align=%s)" % (txt, x, y, y, w, align))
        self.textbox(txt, (x, y, w, h), align)

    _formattedStringClass = FormattedString

    def FormattedString(self, *args, **kwargs):
        """
        Return a string object that can handle text formatting.

        .. showcode:: /../examples/appendGlyphFormattedString.py

        .. autoclass:: drawBot.context.baseContext.FormattedString
            :members:
        """
        return self._formattedStringClass(*args, **kwargs)

    # images

    def image(self, path, x, y=None, alpha=None, pageNumber=None):
        """
        Add an image from a `path` with an `offset` and an `alpha` value.
        This should accept most common file types like pdf, jpg, png, tiff and gif.

        Optionally an `alpha` can be provided, which is a value between 0 and 1.

        Optionally a `pageNumber` can be provided when the path referes to a multi page pdf file.

        .. showcode:: /../examples/image.py
        """
        if isinstance(x, (tuple)):
            if alpha is None and y is not None:
                alpha = y
            x, y = x
        else:
            _deprecatedWarningWrapInTuple("image(\"%s\", (%s, %s), alpha=%s)" % (path, x, y, alpha))

        if alpha is None:
            alpha = 1
        if isinstance(path, self._imageClass):
            path = path._nsImage()
        if isinstance(path, (str, unicode)):
            path = optimizePath(path)
        self._requiresNewFirstPage = True
        self._addInstruction("image", path, (x, y), alpha, pageNumber)

    def imageSize(self, path):
        """
        Return the `width` and `height` of an image.

        .. showcode:: /../examples/imageSize.py
        """
        if isinstance(path, self._imageClass):
            path = path._nsImage()
        if isinstance(path, AppKit.NSImage):
            rep = path.TIFFRepresentation()
            _isPDF = False
        else:
            if isinstance(path, (str, unicode)):
                path = optimizePath(path)
            if path.startswith("http"):
                url = AppKit.NSURL.URLWithString_(path)
            else:
                if not os.path.exists(path):
                    raise DrawBotError("Image does not exist")
                url = AppKit.NSURL.fileURLWithPath_(path)
            _isPDF, _ = isPDF(url)
            # check if the file is an .eps
            _isEPS, epsRep = isEPS(url)
            if _isEPS:
                _isPDF = True
                rep = epsRep
            else:
                rep = AppKit.NSImageRep.imageRepWithContentsOfURL_(url)
        if _isPDF:
            w, h = rep.size()
        else:
            w, h = rep.pixelsWide(), rep.pixelsHigh()
        return w, h

    def imagePixelColor(self, path, (x, y)):
        """
        Return the color `r, g, b, a` of an image at a specified `x`, `y` possition.

        .. showcode:: /../examples/pixelColor.py
        """
        if isinstance(path, (str, unicode)):
            path = optimizePath(path)
        bitmap = _chachedPixelColorBitmaps.get(path)
        if bitmap is None:
            if isinstance(path, self._imageClass):
                source = path._nsImage()
            elif isinstance(path, AppKit.NSImage):
                source = path
            else:
                if path.startswith("http"):
                    url = AppKit.NSURL.URLWithString_(path)
                else:
                    url = AppKit.NSURL.fileURLWithPath_(path)
                source = AppKit.NSImage.alloc().initByReferencingURL_(url)

            bitmap = AppKit.NSBitmapImageRep.imageRepWithData_(source.TIFFRepresentation())
            _chachedPixelColorBitmaps[path] = bitmap

        color = bitmap.colorAtX_y_(x, bitmap.pixelsHigh() - y - 1)
        if color is None:
            return None
        color = color.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
        return color.redComponent(), color.greenComponent(), color.blueComponent(), color.alphaComponent()

    # mov

    def frameDuration(self, seconds):
        """
        When exporting to `mov` or `gif` each frame can have duration set in `seconds`.

        .. showcode:: /../examples/frameDuration.py
        """
        self._requiresNewFirstPage = True
        self._addInstruction("frameDuration", seconds)

    def frameduration(self, seconds):
        _deprecatedWarningLowercase("frameDuration(%s)" % seconds)
        self.frameDuration(seconds)
        
        
    # pdf links
    
    def linkDestination(self, name, x=None, y=None):
        """
        Add a destination point for a link within a PDF.
        """
        if x:
            if len(x) == 2:
                x, y = x
            else: x, y = (None, None)
        self._requiresNewFirstPage = True
        self._addInstruction("linkDestination", name, (x, y))
    
    def linkRect(self, name, (x, y, w, h)):
        """
        Add a rect for a link within a PDF.
        """
        self._requiresNewFirstPage = True
        self._addInstruction("linkRect", name, (x, y, w, h))
        

    # helpers

    def textSize(self, txt, align=None):
        """
        Returns the size of a text with the current settings,
        like `font`, `fontSize` and `lineHeight` as a tuple (width, height).
        """
        if isinstance(txt, (str, unicode)):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        return self._dummyContext.textSize(txt, align)

    def textsize(self, txt, align=None):
        _deprecatedWarningLowercase("textSize(%s, %s)" % (txt, align))
        return self.textSize(txt, align)

    def installedFonts(self):
        """
        Returns a list of all installed fonts.
        """
        return [str(f) for f in AppKit.NSFontManager.sharedFontManager().availableFonts()]

    def installedfonts(self):
        _deprecatedWarningLowercase("installedFonts()")
        return self.installedFonts()

    def installFont(self, path):
        """
        Install a font with a given path and the postscript font name will be returned.
        The postscript font name can be used to set the font as the active font.

        Fonts are installed only for the current process.
        Fonts will not be accesible outside the scope of drawBot.

        All installed fonts will automatically be uninstalled when the script is done.

        .. showcode:: /../examples/installFont.py
        """
        if path in self._tempInstalledFonts:
            return self._tempInstalledFonts[path]

        success, error = self._dummyContext.installFont(path)
        self._addInstruction("installFont", path)

        psName = self._dummyContext._fontNameForPath(path)
        self._tempInstalledFonts[path] = psName

        if not success:
            warnings.warn("install font: %s" % error)
        return psName

    def uninstallFont(self, path):
        """
        Uninstall a font with a given path.
        """
        success, error = self._dummyContext.uninstallFont(path)
        if path in self._tempInstalledFonts:
            del self._tempInstalledFonts[path]
        if not success:
            warnings.warn("uninstall font: %s" % error)
        self._addInstruction("uninstallFont", path)

    def _uninstallAllFonts(self):
        for path in self._tempInstalledFonts:
            self._dummyContext.uninstallFont(path)
        self._tempInstalledFonts = dict()

    def _tryInstallFontFromFontName(self, fontName):
        # check if the fontName is actually a path
        if os.path.exists(fontName):
            fontPath = os.path.abspath(fontName)
            ext = os.path.splitext(fontPath)[1]
            if ext.lower() in [".otf", ".ttf", ".ttc"]:
                fontName = self.installFont(fontPath)
            else:
                raise DrawBotError("Font '%s' is not .ttf, .otf or .ttc." % fontPath)
        return fontName

    def fontAscender(self):
        """
        Returns the current font ascender, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.font.ascender()

    def fontDescender(self):
        """
        Returns the current font descender, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.font.descender()

    def fontXHeight(self):
        """
        Returns the current font x-height, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.font.xHeight()

    def fontCapHeight(self):
        """
        Returns the current font cap height, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.font.capHeight()

    def fontLeading(self):
        """
        Returns the current font leading, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.font.leading()

    def fontLineHeight(self):
        """
        Returns the current line height, based on the current `font` and `fontSize`.
        If a `lineHeight` is set, this value will be returned.
        """
        if self._dummyContext._state.text._lineHeight is not None:
            return self._dummyContext._state.text._lineHeight
        return self._dummyContext._state.text.font.defaultLineHeightForFont()

    _bezierPathClass = BezierPath

    def BezierPath(self, path=None, glyphSet=None):
        """
        Return a BezierPath object.
        This is a reusable object, if you want to draw the same over and over again.

        .. showcode:: /../examples/bezierPath.py

        .. autoclass:: drawBot.context.baseContext.BezierPath
            :members:
        """
        return self._bezierPathClass(path, glyphSet)

    def Bezierpath(self, path=None):
        _deprecatedWarningLowercase("BezierPath()")
        return self.BezierPath()

    _imageClass = ImageObject

    def ImageObject(self, path=None):
        """
        Return a Image object, packed with filters.
        This is a reusable object.

        .. showcode:: /../examples/imageObject.py

        .. autoclass:: drawBot.context.tools.imageObject.ImageObject
            :members:

        """
        return self._imageClass(path)

    def Variable(self, variables, workSpace):
        """
        Build small UI for variables in a script.

        The `workSpace` is usually `globals()`
        as you want to insert the variable in the current workspace.
        It is required that `workSpace` is a `dict` object.

        .. image:: assets/variables.png

        .. showcode:: /../examples/variables.py
        """

        document = AppKit.NSDocumentController.sharedDocumentController().currentDocument()
        if not document:
            raise DrawBotError("There is no document open")
        controller = document.vanillaWindowController
        try:
            controller._variableController.buildUI(variables)
            controller._variableController.show()
        except:
            controller._variableController = VariableController(variables, controller.runCode, document)

        data = controller._variableController.get()
        for v, value in data.items():
            workSpace[v] = value

_drawBotDrawingTool = DrawBotDrawingTool()
