from __future__ import absolute_import

import AppKit
import CoreText
import Quartz

import math
import os
import random

from .context import getContextForFileExt
from .context.baseContext import BezierPath, FormattedString
from .context.dummyContext import DummyContext

from .context.tools.imageObject import ImageObject
from .context.tools import gifTools

from .misc import DrawBotError, warnings, VariableController, optimizePath, isPDF, isEPS, isGIF

from fontTools.misc.py23 import basestring, PY2


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

for key, (w, h) in list(_paperSizes.items()):
    _paperSizes["%sLandscape" % key] = (h, w)


class DrawBotDrawingTool(object):

    def __init__(self):
        self._reset()
        self._isSinglePage = False

    def _get__all__(self):
        return [i for i in dir(self) if not i.startswith("_")] + ["__version__"]

    __all__ = property(_get__all__)

    def _get_version(self):
        try:
            from drawBot import drawBotSettings
            return drawBotSettings.__version__
        except Exception:
            pass
        return ""

    __version__ = property(_get_version)

    def _addToNamespace(self, namespace):
        namespace.update(_getmodulecontents(self, self.__all__))
        namespace.update(_getmodulecontents(random, ["random", "randint", "choice"]))
        namespace.update(_getmodulecontents(math))

    def _addInstruction(self, callback, *args, **kwargs):
        if callback == "newPage":
            self._instructionsStack.append([])
        if not self._instructionsStack:
            self._instructionsStack.append([])
        if self._requiresNewFirstPage and not self._hasPage:
            self._hasPage = True
            self._instructionsStack[-1].insert(0, ("newPage", [self.width(), self.height()], {}))
        self._instructionsStack[-1].append((callback, args, kwargs))

    def _drawInContext(self, context):
        if not self._instructionsStack:
            return
        for instructionSet in self._instructionsStack:
            for callback, args, kwargs in instructionSet:
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
        new._hasPage = self._hasPage
        new._requiresNewFirstPage = self._requiresNewFirstPage
        new._tempInstalledFonts = dict(self._tempInstalledFonts)
        return new

    def newDrawing(self):
        """
        Reset the drawing stack to the clean and empty stack.

        .. downloadcode:: newDrawing.py

            # draw a rectangle
            rect(10, 10, width()-20, height()-20)
            # save it as a pdf
            saveImage("~/Deskopt/aRect.pdf")

            # reset the drawing stack to a clear and empty stack
            newDrawing()

            # draw an oval
            oval(10, 10, width()-20, height()-20)
            # save it as a pdf
            saveImage("~/Deskopt/anOval.pdf")
        """
        self._reset()
        self.installedFonts()

    def endDrawing(self):
        """
        Explicitly tell drawBot the drawing is done.
        This is advised when using drawBot as a standalone module.
        """
        self._uninstallAllFonts()
        gifTools.clearExplodedGifCache()

    # magic variables

    def width(self):
        """
        Returns the width of the current page.
        """
        if self._width is None:
            return 1000
        return self._width

    def _get_width(self):
        warnings.warn("Magic variables are deprecated.")
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
        warnings.warn("Magic variables are deprecated.")
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
        return len(self._instructionsStack)

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

        .. downloadcode:: size.py

            # set a canvas size
            size(200, 200)
            # print out the size of the page
            print width(), height()

            # set a color
            fill(1, 0, 0)
            # use those variables to set a background color
            rect(0, 0, width(), height())

        All supported papersizes: 10x14, 10x14Landscape, A0, A0Landscape, A1, A1Landscape, A2, A2Landscape, A3, A3Landscape, A4, A4Landscape, A4Small, A4SmallLandscape, A5, A5Landscape, B4, B4Landscape, B5, B5Landscape, Executive, ExecutiveLandscape, Folio, FolioLandscape, Ledger, LedgerLandscape, Legal, LegalLandscape, Letter, LetterLandscape, LetterSmall, LetterSmallLandscape, Quarto, QuartoLandscape, Statement, StatementLandscape, Tabloid, TabloidLandscape.
        """
        if self._isSinglePage:
            # dont allow to set a page size
            raise DrawBotError("Cannot set 'size' into a single page.")
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

        .. downloadcode:: newPage.py

            # loop over a range of 100
            for i in range(100):
                # for each loop create a new path
                newPage(500, 500)
                # set a random fill color
                fill(random(), random(), random())
                # draw a rect with the size of the page
                rect(0, 0, width(), height())

        All supported papersizes: 10x14, 10x14Landscape, A0, A0Landscape, A1, A1Landscape, A2, A2Landscape, A3, A3Landscape, A4, A4Landscape, A4Small, A4SmallLandscape, A5, A5Landscape, B4, B4Landscape, B5, B5Landscape, Executive, ExecutiveLandscape, Folio, FolioLandscape, Ledger, LedgerLandscape, Legal, LegalLandscape, Letter, LetterLandscape, LetterSmall, LetterSmallLandscape, Quarto, QuartoLandscape, Statement, StatementLandscape, Tabloid, TabloidLandscape.
        """
        if self._isSinglePage:
            # dont allow to add a page
            raise DrawBotError("Cannot add a 'newPage' into a single page.")
        if width in _paperSizes:
            width, height = _paperSizes[width]
        if width == "screen":
            width, height = AppKit.NSScreen.mainScreen().frame().size
        self._width = width
        self._height = height
        self._hasPage = True
        self._dummyContext = DummyContext()
        self._addInstruction("newPage", width, height)

    def newpage(self, width=None, height=None):
        _deprecatedWarningLowercase("newPage(%s, %s)" % (width, height))
        self.newPage(width, height)

    def pages(self):
        """
        Return all pages.

        .. downloadcode:: pages.py

            # set a size
            size(200, 200)
            # draw a rectangle
            rect(10, 10, 100, 100)
            # create a new page
            newPage(200, 300)
            # set a color
            fill(1, 0, 1)
            # draw a rectangle
            rect(10, 10, 100, 100)
            # create a new page
            newPage(200, 200)
            # set a color
            fill(0, 1, 0)
            # draw a rectangle
            rect(10, 10, 100, 100)

            # get all pages
            allPages = pages()
            # count how many pages are available
            print len(allPages)

            # use the `with` statement
            # to set a page as current context
            with allPages[1]:
                # draw into the selected page
                fontSize(30)
                text("Hello World", (10, 150))

            # loop over allpages
            for page in allPages:
                # set the page as current context
                with page:
                    # draw an oval in each of them
                    oval(110, 10, 30, 30)
        """
        from .drawBotPageDrawingTools import DrawBotPage
        instructions = []
        for instructionSet in self._instructionsStack:
            for callback, _, _ in instructionSet:
                if callback == "newPage":
                    instructions.append(instructionSet)
                    break
        return tuple(DrawBotPage(instructionSet) for instructionSet in instructions)

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

        .. downloadcode:: saveImage.py

            # set the canvas size
            size(150, 100)

            # draw a background
            rect(10, 10, width()-20, height()-20)

            # set a fill
            fill(1)
            # draw some text
            text("Hello World!", (20, 40))
            # save it as a png and pdf on the current users desktop
            saveImage(["~/Desktop/firstImage.png", "~/Desktop/firstImage.pdf"])
        """
        if isinstance(paths, basestring):
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
                raise DrawBotError("Could not find a supported context for: '%s'" % ext)
            self._drawInContext(context)
            context.saveImage(path, multipage)

    def saveimage(self, paths):
        _deprecatedWarningLowercase("saveImage()")
        self.saveImage(paths)

    def printImage(self, pdf=None):
        """
        Export the canvas to a printing dialog, ready to print.

        Optionally a `pdf` object can be provided.

        .. downloadcode:: printImage.py

            # set A4 page size
            size(595, 842)
            # draw something
            oval(0, 0, width(), height())
            # send it to the printer
            printImage()
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
        from .context.drawBotContext import DrawBotContext
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

        .. downloadcode:: rect.py

            # draw a rectangle
            #    x    y    w    h
            rect(100, 100, 200, 200)
        """
        self._requiresNewFirstPage = True
        self._addInstruction("rect", x, y, w, h)

    def oval(self, x, y, w, h):
        """
        Draw an oval from position x, y with the given width and height.

        .. downloadcode:: oval.py

            # draw an oval
            #    x    y    w    h
            oval(100, 100, 200, 200)
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

    def moveTo(self, xy):
        """
        Move to a point `x`, `y`.
        """
        x, y = xy
        self._requiresNewFirstPage = True
        self._addInstruction("moveTo", (x, y))

    def moveto(self, x, y):
        _deprecatedWarningLowercase("moveTo((%s, %s))" % (x, y))
        self.moveTo((x, y))

    def lineTo(self, xy):
        """
        Line to a point `x`, `y`.
        """
        x, y = xy
        self._requiresNewFirstPage = True
        self._addInstruction("lineTo", (x, y))

    def lineto(self, x, y):
        _deprecatedWarningLowercase("lineTo((%s, %s))" % (x, y))
        self.lineTo((x, y))

    def curveTo(self, xy1, xy2, xy3):
        """
        Curve to a point `x3`, `y3`.
        With given bezier handles `x1`, `y1` and `x2`, `y2`.
        """
        x1, y1 = xy1
        x2, y2 = xy2
        x3, y3 = xy3
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

    def arcTo(self, xy1, xy2, radius):
        """
        Arc from one point to an other point with a given `radius`.
        """
        x1, y1 = xy1
        x2, y2 = xy2
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

        .. downloadcode:: line.py

            # set a stroke color
            stroke(0)
            # draw a line between two given points
            line((100, 100), (200, 200))
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

        .. downloadcode:: polygon.py

            # draw a polygon with x-amount of points
            polygon((100, 100), (100, 200), (200, 200), (120, 180), close=True)
        """
        try:
            a, b = x
        except TypeError:
            args = [args[i:i + 2] for i in range(0, len(args), 2)]
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

        .. downloadcode:: colorSpace.py

            # set a color
            r, g, b, a = 0.74, 0.51, 1.04, 1

            # get all available color spaces
            colorSpaces = listColorSpaces()

            x = 0
            w = width() / len(colorSpaces)

            # start loop
            for space in colorSpaces:

                # set a color space
                colorSpace(space)
                # set the color
                fill(r, g, b)
                # draw a rect
                rect(x, 0, w, height())
                x += w
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

        .. downloadcode:: blendMode.py

            # set a blend mode
            blendMode("multiply")

            # set a color
            cmykFill(1, 0, 0, 0)
            # draw a rectangle
            rect(10, 10, 100, 100)
            # set an other color
            cmykFill(0, 1, 0, 0)
            # overlap a second rectangle
            rect(60, 60, 100, 100)
        """
        if operation not in self._dummyContext._blendModeMap.keys():
            raise DrawBotError("blend mode must be %s" % (", ".join(self._dummyContext._blendModeMap.keys())))
        self._requiresNewFirstPage = True
        self._addInstruction("blendMode", operation)

    def fill(self, r=None, g=None, b=None, alpha=1):
        """
        Sets the fill color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.

        .. downloadcode:: fill.py

            fill(1, 0, 0, .5)
            # draw a rect
            rect(0, 10, 10, 100)

            # only set a gray value
            fill(0)
            # draw a rect
            rect(10, 10, 10, 100)

            # only set a gray value with an alpha
            fill(0, .5)
            # draw a rect
            rect(20, 10, 10, 100)

            # set rgb with no alpha
            fill(1, 0, 0)
            # draw a rect
            rect(30, 10, 10, 100)

            # set rgb with an alpha value
            fill(1, 0, 0, .5)
            # draw a rect
            rect(40, 10, 10, 100)
        """
        self._requiresNewFirstPage = True
        self._addInstruction("fill", r, g, b, alpha)

    def stroke(self, r=None, g=None, b=None, alpha=1):
        """
        Sets the stroke color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.

        .. downloadcode:: stroke.py

            # set the fill to none
            fill(None)
            stroke(1, 0, 0, .3)
            # draw a rect
            rect(10, 10, 10, 100)

            # only set a gray value
            stroke(0)
            # draw a rect
            rect(30, 10, 10, 100)

            # only set a gray value with an alpha
            stroke(0, .5)
            # draw a rect
            rect(50, 10, 10, 100)

            # set rgb with no alpha
            stroke(1, 0, 0)
            # draw a rect
            rect(70, 10, 10, 100)

            # set rgb with an alpha value
            stroke(1, 0, 0, .5)
            # draw a rect
            rect(90, 10, 10, 100)
        """
        self._requiresNewFirstPage = True
        self._addInstruction("stroke", r, g, b, alpha)

    def cmykFill(self, c, m=None, y=None, k=None, alpha=1):
        """
        Set a fill using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK fill color. Each value must be a float between 0.0 and 1.0.

        .. downloadcode:: cmykFill.py

            x, y = 0, 0
            s = 100

            # cyan
            cmykFill(1, 0, 0, 0)
            rect(x, y, s, s)
            x += s

            # magenta
            cmykFill(0, 1, 0, 0)
            rect(x, y, s, s)
            x += s

            # yellow
            cmykFill(0, 0, 1, 0)
            rect(x, y, s, s)
            x += s

            # black
            cmykFill(0, 0, 0, 1)
            rect(x, y, s, s)
        """
        self._requiresNewFirstPage = True
        self._addInstruction("cmykFill", c, m, y, k, alpha)

    def cmykfill(self, c, m=None, y=None, k=None, alpha=1):
        _deprecatedWarningLowercase("cmykFill(%s, %s, %s, %s, alpha=%s)" % (c, m, y, k, alpha))
        self.cmykFill(c, m, y, k)

    def cmykStroke(self, c, m=None, y=None, k=None, alpha=1):
        """
        Set a stroke using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK stroke color. Each value must be a float between 0.0 and 1.0.

        .. downloadcode:: cmykStroke.py

            x, y = 20, 20
            lines = 20

            colorStep = 1.00 / lines

            strokeWidth(10)

            for i in range(lines):
                cmykStroke(0, i * colorStep, 1, 0)
                line((x, y), (x, y + 200))
                translate(12, 0)
        """
        self._requiresNewFirstPage = True
        self._addInstruction("cmykStroke", c, m, y, k, alpha)

    def cmykstroke(self, c, m=None, y=None, k=None, alpha=1):
        _deprecatedWarningLowercase("cmykStroke(%s, %s, %s, %s, alpha=%s)" % (c, m, y, k, alpha))
        self.cmykStroke(c, m, y, k)

    def shadow(self, offset, blur=None, color=None):
        """
        Adds a shadow with an `offset` (x, y), `blur` and a `color`.
        The `color` argument must be a tuple similarly as `fill`.
        The `offset`and `blur` argument will be drawn independent of the current context transformations.

        .. downloadcode:: shadow.py

            # a red shadow with some blur and a offset
            shadow((3, 3), 10, (1, 0, 0))

            # draw a rect
            rect(100, 100, 30, 30)
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

        .. downloadcode:: cmykShadow.py

            # a red shadow with some blur and a offset
            cmykShadow((3, 3), 10, (1, 0, 0, 0))

            # draw a rect
            rect(100, 100, 30, 30)
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

        .. downloadcode:: linearGradient.py

            # set a gradient as the fill color
            linearGradient(
                (100, 100),                         # startPoint
                (200, 200),                         # endPoint
                [(1, 0, 0), (0, 0, 1), (0, 1, 0)],  # colors
                [0, .2, 1]                          # locations
                )
            # draw a rectangle
            rect(100, 100, 100, 100)
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

        .. downloadcode:: cmykLinearGradient.py

            # set a gradient as the fill color
            linearGradient(
                (100, 100),                                     # startPoint
                (200, 200),                                     # endPoint
                [(1, 0, 0, 1), (0, 0, 1, 0), (0, 1, 0, .2)],    # colors
                [0, .2, 1]                                      # locations
                )
            # draw a rectangle
            rect(100, 100, 100, 100)
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

        .. downloadcode:: radialGradient.py

            # set a gradient as the fill color
            radialGradient(
                (100, 100),                         # startPoint
                (200, 200),                         # endPoint
                [(1, 0, 0), (0, 0, 1), (0, 1, 0)],  # colors
                [0, .2, 1],                         # locations
                0,                                  # startRadius
                100                                 # endRadius
                )
            # draw a rectangle
            rect(100, 100, 100, 100)
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

        .. downloadcode:: cmykRadialGradient.py

            # set a gradient as the fill color
            cmykRadialGradient(
                (100, 100),                                     # startPoint
                (200, 200),                                     # endPoint
                [(1, 0, 0, 1), (0, 0, 1, 0), (0, 1, 0, .2)],    # colors
                [0, .2, 1],                                     # locations
                0,                                              # startRadius
                100                                             # endRadius
                )
            # draw a rectangle
            rect(100, 100, 100, 100)
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

        .. downloadcode:: strokeWidth.py

            # set no fill
            fill(None)
            # set black as the stroke color
            stroke(0)
            # loop over a range of 10
            for i in range(10):
                # in each loop set the stroke width
                strokeWidth(i)
                # draw a line
                line((100, 100), (200, 200))
                # and translate the canvas
                translate(15, 0)
        """
        self._requiresNewFirstPage = True
        self._addInstruction("strokeWidth", value)

    def strokewidth(self, value):
        _deprecatedWarningLowercase("strokeWidth(%s)" % value)
        self.strokeWidth(value)

    def miterLimit(self, value):
        """
        Set a miter limit. Used on corner points.

        .. downloadcode:: miterLimit.py

            # create a path
            path = BezierPath()

            # move to a point
            path.moveTo((100, 100))
            # line to a point
            path.lineTo((100, 200))
            path.lineTo((120, 100))

            # set stroke color to black
            stroke(0)
            # set no fill
            fill(None)
            # set the width of the stroke
            strokeWidth(10)

            # draw the path
            drawPath(path)

            # move the canvas
            translate(100, 0)

            # set a miter limit
            miterLimit(50)

            # draw the same path again
            drawPath(path)
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

        .. downloadcode:: lineJoin.py

            # set no fill
            fill(None)
            # set the stroke color to black
            stroke(0)
            # set a stroke width
            strokeWidth(10)
            # set a miter limit
            miterLimit(30)

            # create a bezier path
            path = BezierPath()
            # move to a point
            path.moveTo((100, 100))
            # line to a point
            path.lineTo((100, 200))
            path.lineTo((110, 100))

            # set a line join style
            lineJoin("miter")
            # draw the path
            drawPath(path)
            # translate the canvas
            translate(100, 0)

            # set a line join style
            lineJoin("round")
            # draw the path
            drawPath(path)
            # translate the canvas
            translate(100, 0)

            # set a line join style
            lineJoin("bevel")
            # draw the path
            drawPath(path)
            # translate the canvas
            translate(100, 0)
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

        .. downloadcode:: lineCap.py

            # set stroke color to black
            stroke(0)
            # set a strok width
            strokeWidth(10)

            # translate the canvas
            translate(100, 100)

            # set a line cap style
            lineCap("butt")
            # draw a line
            line((0, 30), (0, 200))

            # rotate the canvas
            rotate(-30)
            # set a line cap style
            lineCap("square")
            # draw a line
            line((0, 30), (0, 200))

            # rotate the canvase
            rotate(-30)
            # set a line cap style
            lineCap("round")
            # draw a line
            line((0, 30), (0, 200))
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

        .. downloadcode:: lineDash.py

            # set stroke color to black
            stroke(0)
            # set a strok width
            strokeWidth(10)

            # translate the canvas
            translate(100, 100)

            # set a line cap style
            lineCap("butt")
            # draw a line
            line((0, 30), (0, 200))

            # rotate the canvas
            rotate(-30)
            # set a line cap style
            lineCap("square")
            # draw a line
            line((0, 30), (0, 200))

            # rotate the canvase
            rotate(-30)
            # set a line cap style
            lineCap("round")
            # draw a line
            line((0, 30), (0, 200))
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

        The font name is returned, which is handy when the font was loaded
        from a path.

        ::

            font("Times-Italic")
        """
        fontName = self._tryInstallFontFromFontName(fontName)
        fontName = str(fontName)
        self._dummyContext.font(fontName, fontSize)
        self._addInstruction("font", fontName, fontSize)
        return fontName

    def fallbackFont(self, fontName):
        """
        Set a fallback font, this is used whenever a glyph is not available in the current font.

        ::

            fallbackFont("Times")
        """
        fontName = self._tryInstallFontFromFontName(fontName)
        fontName = str(fontName)
        dummyFont = AppKit.NSFont.fontWithName_size_(fontName, 10)
        if dummyFont is None:
            raise DrawBotError("Fallback font '%s' is not available" % fontName)
        self._dummyContext.fallbackFont(fontName)
        self._addInstruction("fallbackFont", fontName)
        return fontName

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

        .. downloadcode:: lineHeight.py

            lineHeight(20)
            textBox("Hello\\nWorld", (10, 10, 100, 100))
        """
        self._dummyContext.lineHeight(value)
        self._addInstruction("lineHeight", value)

    def lineheight(self, value):
        _deprecatedWarningLowercase("lineHeight(%s)" % value)
        self.lineHeight(value)

    def tracking(self, value):
        """
        Set the tracking between characters.

        .. downloadcode:: tracking.py

            # set tracking
            tracking(100)
            # set font size
            fontSize(100)
            # draw some text
            text("hello", (100, 200))
            # disable tracking
            tracking(None)
            # draw some text
            text("world", (100, 100))
        """
        self._dummyContext.tracking(value)
        self._addInstruction("tracking", value)

    def baselineShift(self, value):
        """
        Set the shift of the baseline.
        """
        self._dummyContext.baselineShift(value)
        self._addInstruction("baselineShift", value)

    def underline(self, value):
        """
        Set the underline value.
        Underline must be `single` or `None.

        .. downloadcode:: underline.py

            underline("single")
            fontSize(140)
            text("hello underline", (50, 50))
        """
        if value is not None and value not in self._dummyContext._textUnderlineMap:
            raise DrawBotError("underline must be %s" % (", ".join(sorted(self._dummyContext._textUnderlineMap.keys()))))
        self._dummyContext.underline(value)
        self._addInstruction("underline", value)

    def hyphenation(self, value):
        """
        Set hyphenation, `True` or `False`.

        .. downloadcode:: hyphenation.py

            txt = '''Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi. Nam liber tempor cum soluta nobis eleifend option congue nihil imperdiet doming id quod mazim placerat facer possim assum. Typi non habent claritatem insitam; est usus legentis in iis qui facit eorum claritatem. Investigationes demonstraverunt lectores legere me lius quod ii legunt saepius. Claritas est etiam processus dynamicus, qui sequitur mutationem consuetudium lectorum. Mirum est notare quam littera gothica, quam nunc putamus parum claram, anteposuerit litterarum formas humanitatis per seacula quarta decima et quinta decima. Eodem modo typi, qui nunc nobis videntur parum clari, fiant sollemnes in futurum.'''

            hyphenation(True)
            textBox(txt, (10, 10, 200, 200))
        """
        self._dummyContext.hyphenation(value)
        self._checkLanguageHyphenation()
        self._addInstruction("hyphenation", value)

    def tabs(self, *tabs):
        """
        Set tabs, tuples of (`float`, `alignment`)
        Aligment can be `"left"`, `"center"`, `"right"` or any other character.
        If a character is provided the alignment will be `right` and centered on the specified character.

        .. downloadcode:: tabs.py

            t = " hello w o r l d"
            # replace all spaces by tabs
            t = t.replace(" ", "\t")
            # set some tabs
            tabs((85, "center"), (232, "right"), (300, "left"))
            # draw the string
            text(t, (10, 10))
            # reset all tabs
            tabs(None)
            # draw the same string
            text(t, (10, 50))
        """
        if tabs and tabs[0] is None:
            self._dummyContext.tabs(None)
            self._addInstruction("tabs", None)
            return
        self._dummyContext.tabs(*tabs)
        self._addInstruction("tabs", *tabs)

    def language(self, language):
        """
        Set the preferred language as language tag or None to use the default language.

        Support is depending on local OS.

        .. downloadcode:: language.py

            # a long dutch word
            word = "paardenkop"
            # a box where we draw in
            box = (10, 10, 100, 100)

            # set font size
            fontSize(28)
            # enable hyphenation
            hyphenation(True)
            # draw the text with no language set
            textBox(word, box)
            # set language to dutch (nl)
            language("nl")
            # shift up a bit
            translate(0, 150)
            # darw the text again with a language set
            textBox(word, box)
        """
        self._dummyContext.language(language)
        self._checkLanguageHyphenation()
        self._addInstruction("language", language)

    def listLanguages(self):
        """
        List all available languages as dictionary mapped to a readable language/dialect name.
        """
        loc = AppKit.NSLocale.currentLocale()
        return {tag: loc.displayNameForKey_value_(AppKit.NSLocaleIdentifier, tag) for tag in AppKit.NSLocale.availableLocaleIdentifiers()}

    def _checkLanguageHyphenation(self):
        language = self._dummyContext._state.text._language
        if language and self._dummyContext._state.hyphenation:
            locale = CoreText.CFLocaleCreate(None, language)
            if not CoreText.CFStringIsHyphenationAvailableForLocale(locale):
                warnings.warn("Language '%s' has no hyphenation available." % language)

    def openTypeFeatures(self, *args, **features):
        """
        Enable OpenType features.

        Supported OpenType tags:

        ::

            c2pc, c2sc, calt, case, cpsp, cswh, dlig, frac, liga, lnum, onum, ordn, pnum, rlig, sinf, smcp, ss01, ss02, ss03, ss04, ss05, ss06, ss07, ss08, ss09, ss10, ss11, ss12, ss13, ss14, ss15, ss16, ss17, ss18, ss19, ss20, subs, sups, swsh, titl, tnum

        .. downloadcode:: openTypeFeatures.py

            # set a font
            font("ACaslonPro-Regular")
            # set the font size
            fontSize(50)
            # draw a string
            text("aa1465", (100, 200))
            # enable some OpenType features
            openTypeFeatures(lnum=True, smcp=True)
            # draw the same string
            text("aa1465", (100, 100))
        """
        self._dummyContext.openTypeFeatures(*args, **features)
        self._addInstruction("openTypeFeatures", *args, **features)

    def listOpenTypeFeatures(self, fontName=None):
        """
        List all OpenType feature tags for the current font.

        Optionally a `fontName` can be given. If a font path is given the font will be installed and used directly.
        """
        return self._dummyContext._state.text.listOpenTypeFeatures(fontName)

    def fontVariations(self, *args, **axes):
        """
        Pick a variation by axes values.

        .. downloadcode:: fontVariations.py

            # pick a font
            font("Skia")
            # pick a font size
            fontSize(200)
            # list all axis from the current font
            for axis, data in listFontVariations().items():
                print axis, data
            # pick a variation from the current font
            fontVariations(wght=.6)
            # draw text!!
            text("Hello Q", (100, 100))
            # pick a variation from the current font
            fontVariations(wght=3, wdth=1.2)
            # draw text!!
            text("Hello Q", (100, 300))
        """
        self._dummyContext.fontVariations(*args, **axes)
        self._addInstruction("fontVariations", *args, **axes)

    def listFontVariations(self, fontName=None):
        """
        List all variation axes for the current font.

        Optionally a `fontName` can be given. If a font path is given the font will be installed and used directly.
        """
        return self._dummyContext._state.text.listFontVariations(fontName)

    # drawing text

    def text(self, txt, x, y=None, align=None):
        """
        Draw a text at a provided position.

        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"` and `"right"`.

        The default alignment is `left`.

        Optionally `txt` can be a `FormattedString`.

        .. downloadcode:: text.py

            font("Times-Italic")
            text("hallo, I'm Times", (100, 100))
        """
        if PY2 and isinstance(txt, basestring):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        if y is None:
            x, y = x
        else:
            warnings.warn("position must a tuple: text('%s', (%s, %s))" % (txt, x, y))
        if align is None:
            align = "left"
        elif align not in ("left", "center", "right"):
            raise DrawBotError("align must be left, right, center")
        attrString = self._dummyContext.attributedString(txt, align=align)
        w, h = attrString.size()
        if align == "right":
            x -= w
        elif align == "center":
            x -= w * .5
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = Quartz.CGPathCreateMutable()
        Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CoreText.CTFrameGetLines(box)
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        if origins:
            y -= origins[0][1]
        self.textBox(txt, (x, y - h, w, h * 2), align=align)

    def textOverflow(self, txt, box, align=None):
        """
        Returns the overflowed text without drawing the text.

        A `box` could be a `(x, y, w, h)` or a bezierPath object.

        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"`, `"right"` and `"justified"`.

        The default alignment is `left`.

        Optionally `txt` can be a `FormattedString`.
        Optionally `box` can be a `BezierPath`.
        """
        if PY2 and isinstance(txt, basestring):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        if isinstance(txt, self._formattedStringClass):
            txt = txt.copy()
        if align is None:
            align = "left"
        elif align not in self._dummyContext._textAlignMap.keys():
            raise DrawBotError("align must be %s" % (", ".join(self._dummyContext._textAlignMap.keys())))
        return self._dummyContext.clippedText(txt, box, align)

    def textBox(self, txt, box, align=None):
        """
        Draw a text in a provided rectangle.

        A `box` could be a `(x, y, w, h)` or a bezierPath object.

        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"`, `"right"` and `"justified"`.

        If the text overflows the rectangle, the overflowed text is returned.

        The default alignment is `left`.

        .. downloadcode:: textBox.py

            x, y, w, h = 100, 100, 256, 174

            fill(1, 0, 0)
            rect(x, y, w, h)
            fill(1)
            fontSize(50)
            overflow = textBox("hallo, this text is a bit to long",
                            (x, y, w, h), align="center")
            print overflow

        The returned overflow can be used to add new pages until all text is set:

        .. downloadcode:: overflowText.py

            t = '''DrawBot is a powerful, free application for MacOSX that invites you to write simple Python scripts to generate two-dimensional graphics. The builtin graphics primitives support rectangles, ovals, (bezier) paths, polygons, text objects and transparency.
            DrawBot is an ideal tool to teach the basics of programming. Students get colorful graphic treats while getting familiar with variables, conditional statements, functions and what have you. Results can be saved in a selection of different file formats, including as high resolution, scaleable PDF.
            DrawBot has proven itself as part of the curriculum at selected courses at the Royal Academy in The Hague.'''

            # setting some variables
            # setting the size
            x, y, w, h = 10, 10, 480, 480

            # setting the color change over different frames
            coloradd = .1

            # setting the start background color only red and blue
            r = .3
            b = 1

            # start a loop and run as long there is t variable has some text
            while len(t):
                # create a new page
                newPage(500, 500)
                # set a frame duration
                frameDuration(3)
                # set the background fill
                fill(r, 0, b)
                # draw the background
                rect(x, y, w, h)
                # set a fill color
                fill(0)
                # set a font with a size
                font("DrawBot-Bold", randint(50, 100))
                # pick some random colors
                rr = random()
                gg = random()
                bb = random()
                # set a gradient as fill
                radialGradient((250, 250), (250, 250), [(rr, gg, bb), (1-rr, 1-gg, 1-bb)], startRadius=0, endRadius=250)

                # draw the text in a box with the gradient fill
                t = textBox(t, (x, y, w, h))

                # setting the color for the next frame
                r += coloradd
                b -= coloradd

                # set a font
                font("DrawBot-Bold", 20)
                # get the page count text size as a (width, height) tuple
                tw, th = textSize("%s" % pageCount())
                # draw the text
                textBox("%s" % pageCount(), (10, 10, 480, th), align="center")

            saveImage("~/Desktop/drawbot.mov")

        Another example, this time using a bezierPath as a text envelope:

        .. downloadcode:: textBoxInPath.py

            # create a fresh bezier path
            path = BezierPath()
            # draw some text
            # the text will be converted to curves
            path.text("a", font="Helvetica-Bold", fontSize=500)
            # set an indent
            indent = 50
            # calculate the width and height of the path
            minx, miny, maxx, maxy = path.bounds()
            w = maxx - minx
            h = maxy - miny
            # calculate the box where we want to draw the path in
            boxWidth = width() - indent * 2
            boxHeight = height() - indent * 2
            # calculate a scale based on the given path bounds and the box
            s = min([boxWidth / float(w), boxHeight / float(h)])
            # translate to the middle
            translate(width()*.5, height()*.5)
            # set the scale
            scale(s)
            # translate the negative offset, letter could have overshoot
            translate(-minx, -miny)
            # translate with half of the width and height of the path
            translate(-w*.5, -h*.5)
            # draw the path
            drawPath(path)
            # set a font
            font("Helvetica-Light")
            # set a font size
            fontSize(5)
            # set white as color
            fill(1)
            # draw some text in the path
            textBox("abcdefghijklmnopqrstuvwxyz"*30000, path)
        """
        if PY2 and isinstance(txt, basestring):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        if align is None:
            align = "left"
        elif align not in self._dummyContext._textAlignMap.keys():
            raise DrawBotError("align must be %s" % (", ".join(self._dummyContext._textAlignMap.keys())))
        self._requiresNewFirstPage = True
        self._addInstruction("textBox", txt, box, align)
        return self._dummyContext.clippedText(txt, box, align)

    def textbox(self, txt, x, y, w, h, align=None):
        _deprecatedWarningLowercase("textBox('%s', (%s, %s, %s, %s), align=%s)" % (txt, x, y, y, w, align))
        return self.textBox(txt, (x, y, w, h), align)

    def textBoxBaselines(self, txt, box, align=None):
        """
        Returns a list of `x, y` coordinates
        indicating the start of each line
        for a given `text` in a given `box`.

        A `box` could be a `(x, y, w, h)` or a bezierPath object.

        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"`, `"right"` and `"justified"`.
        """
        if PY2 and isinstance(txt, basestring):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        path, (x, y) = self._dummyContext._getPathForFrameSetter(box)
        attrString = self._dummyContext.attributedString(txt)
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CoreText.CTFrameGetLines(box)
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        return [(x + o.x, y + o.y) for o in origins]

    _formattedStringClass = FormattedString

    def FormattedString(self, *args, **kwargs):
        """
        Return a string object that can handle text formatting.

        .. downloadcode:: formattedString.py

            # create a formatted string
            txt = FormattedString()

            # adding some text with some formatting
            txt.append("hello", font="Helvetica", fontSize=100, fill=(1, 0, 0))
            # adding more text
            txt.append("world", font="Times-Italic", fontSize=50, fill=(0, 1, 0))

            # setting a font
            txt.font("Helvetica-Bold")
            txt.fontSize(75)
            txt += "hello again"

            # drawing the formatted string
            text(txt, (10, 10))


            # create a formatted string
            txt = FormattedString()

            # adding some text with some formatting
            txt.append("hello", font="ACaslonPro-Regular", fontSize=50)
            # adding more text with an
            txt.append("world", font="ACaslonPro-Regular", fontSize=50, openTypeFeatures=dict(smcp=True))

            text(txt, (10, 110))

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

        .. downloadcode:: image.py

            # the path can be a path to a file or a url
            image("http://f.cl.ly/items/1T3x1y372J371p0v1F2Z/drawBot.jpg", (100, 100), alpha=.3)
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
        if isinstance(path, basestring):
            path = optimizePath(path)
        self._requiresNewFirstPage = True
        self._addInstruction("image", path, (x, y), alpha, pageNumber)

    def imageSize(self, path, pageNumber=None):
        """
        Return the `width` and `height` of an image.

        .. downloadcode:: imageSize.py

            print imageSize("http://f.cl.ly/items/1T3x1y372J371p0v1F2Z/drawBot.jpg")
        """
        if isinstance(path, self._imageClass):
            # its an drawBot.ImageObject, just return the size from that obj
            return path.size()

        _hasPixels = False

        if isinstance(path, AppKit.NSImage):
            # its an NSImage
            rep = path
        else:
            if isinstance(path, basestring):
                path = optimizePath(path)
            if path.startswith("http"):
                url = AppKit.NSURL.URLWithString_(path)
            else:
                if not os.path.exists(path):
                    raise DrawBotError("Image does not exist")
                url = AppKit.NSURL.fileURLWithPath_(path)
            # check if the file is an .pdf
            _isPDF, pdfDocument = isPDF(url)
            # check if the file is an .eps
            _isEPS, epsRep = isEPS(url)
            # check if the file is an .gif
            _isGIF, gifRep = isGIF(url)
            if _isEPS:
                rep = epsRep
            elif _isPDF and pageNumber is None:
                rep = AppKit.NSImage.alloc().initByReferencingURL_(url)
            elif _isGIF and pageNumber is not None:
                rep = gifTools.gifFrameAtIndex(url, pageNumber - 1)
            elif _isPDF and pageNumber is not None:
                page = pdfDocument.pageAtIndex_(pageNumber - 1)
                # this is probably not the fastest method...
                rep = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
            else:
                _hasPixels = True
                rep = AppKit.NSImageRep.imageRepWithContentsOfURL_(url)

        if _hasPixels:
            w, h = rep.pixelsWide(), rep.pixelsHigh()
        else:
            w, h = rep.size()
        return w, h

    def imagePixelColor(self, path, xy):
        """
        Return the color `r, g, b, a` of an image at a specified `x`, `y` possition.

        .. downloadcode:: pixelColor.py

            # path to the image
            path = u"http://f.cl.ly/items/1T3x1y372J371p0v1F2Z/drawBot.jpg"

            # get the size of the image
            w, h = imageSize(path)

            # setup a variable for the font size as for the steps
            s = 15

            # shift it up a bit
            translate(100, 100)

            # set a font with a size
            font("Helvetica-Bold")
            fontSize(s)

            # loop over the width of the image
            for x in range(0, w, s):
                # loop of the height of the image
                for y in range(0, h, s):
                    # get the color
                    color = imagePixelColor(path, (x, y))
                    if color:
                        r, g, b, a = color
                        # set the color
                        fill(r, g, b, a)
                        # draw some text
                        text("W", (x, y))
        """
        x, y = xy
        if isinstance(path, basestring):
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

    def numberOfPages(self, path):
        path = optimizePath(path)
        if path.startswith("http"):
            url = AppKit.NSURL.URLWithString_(path)
        else:
            url = AppKit.NSURL.fileURLWithPath_(path)
        pdf = Quartz.CGPDFDocumentCreateWithURL(url)
        if pdf:
            return Quartz.CGPDFDocumentGetNumberOfPages(pdf)
        _isGIF, _ = isGIF(url)
        if _isGIF:
            frameCount = gifTools.gifFrameCount(url)
            if frameCount:
                return frameCount
        return None

    # mov

    def frameDuration(self, seconds):
        """
        When exporting to `mov` or `gif` each frame can have duration set in `seconds`.

        .. downloadcode:: frameDuration.py

            # setting some variables
            # size of the pages / frames
            w, h = 200, 200
            # frame per seconds
            fps = 30
            # duration of the movie
            seconds = 3
            # calculate the lenght of a single frame
            duration = 1 / fps
            # calculate the amount of frames needed
            totalFrames = seconds * fps

            # title page
            newPage(w, h)
            # set frame duration to 1 second
            frameDuration(1)
            # pick a font and font size
            font("Helvetica", 40)
            # draw the title text in a box
            textBox("Rotated square", (0, 0, w, h * .8), align="center")

            # loop over the amount of frames needed
            for i in range(totalFrames):
                # create a new page
                newPage(w, h)
                # set the frame duration
                frameDuration(duration)
                # set a fill color
                fill(1, 0, 0)
                # translate to the center of the page
                translate(w / 2, h / 2)
                # rotate around the center
                rotate(i*10)
                # draw the rect
                rect(-50, -50, 50, 50)

            # save the image as a mov on the desktop
            saveImage('~/Desktop/frameDuration.mov')
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

        The destination position will be set independent of the current context transformations.
        """
        if x:
            if len(x) == 2:
                x, y = x
            else:
                x, y = (None, None)
        self._requiresNewFirstPage = True
        self._addInstruction("linkDestination", name, (x, y))

    def linkRect(self, name, xywh):
        """
        Add a rect for a link within a PDF.

        The link rectangle will be set independent of the current context transformations.
        """
        x, y, w, h = (x, y, w, h)
        self._requiresNewFirstPage = True
        self._addInstruction("linkRect", name, (x, y, w, h))

    # helpers

    def textSize(self, txt, align=None, width=None, height=None):
        """
        Returns the size of a text with the current settings,
        like `font`, `fontSize` and `lineHeight` as a tuple (width, height).

        Optionally a `width` constrain or `height` constrain can be provided
        to calculate the lenght or width of text with the given constrain.
        """
        if PY2 and isinstance(txt, basestring):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        if width is not None and height is not None:
            raise DrawBotError("Calculating textSize can only have one constrain, either width or height must be None")
        return self._dummyContext.textSize(txt, align, width, height)

    def textsize(self, txt, align=None):
        _deprecatedWarningLowercase("textSize(%s, %s)" % (txt, align))
        return self.textSize(txt, align)

    def installedFonts(self, supportsCharacters=None):
        """
        Returns a list of all installed fonts.

        Optionally a string with `supportsCharacters` can be provided,
        the list of available installed fonts will be filterd by
        support of these characters,
        """
        if supportsCharacters is not None:
            if len(supportsCharacters) == 0:
                raise DrawBotError("supportsCharacters must contain at least one character")
            characterSet = AppKit.NSCharacterSet.characterSetWithCharactersInString_(supportsCharacters)
            fontAttributes = {CoreText.NSFontCharacterSetAttribute: characterSet}
            fontDescriptor = CoreText.CTFontDescriptorCreateWithAttributes(fontAttributes)
            descriptions = fontDescriptor.matchingFontDescriptorsWithMandatoryKeys_(None)
            return [str(description[CoreText.NSFontNameAttribute]) for description in descriptions]
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

        .. downloadcode:: installFont.py

            # set the path to a font file
            path = "path/to/font/file.otf"
            # install the font
            fontName = installFont(path)
            # set the font
            font(fontName, 200)
            # draw some text
            text("Hello World", (10, 10))
            # uninstall font
            uninstallFont(path)
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

    def fontContainsCharacters(self, characters):
        """
        Return a bool if the current font contains the provided `characters`.
        Characters is a string containing one or more characters.
        """
        return self._dummyContext._state.text.fontContainsCharacters(characters)

    def fontContainsGlyph(self, glyphName):
        """
        Return a bool if the current font contains a provided glyph name.
        """
        return self._dummyContext._state.text.fontContainsGlyph(glyphName)

    def fontFilePath(self):
        """
        Return the path to the file of the current font.
        """
        return self._dummyContext._state.text.fontFilePath()

    def listFontGlyphNames(self):
        """
        Return a list of glyph names supported by the current font.
        """
        return self._dummyContext._state.text.listFontGlyphNames()

    def fontAscender(self):
        """
        Returns the current font ascender, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.fontAscender()

    def fontDescender(self):
        """
        Returns the current font descender, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.fontDescender()

    def fontXHeight(self):
        """
        Returns the current font x-height, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.fontXHeight()

    def fontCapHeight(self):
        """
        Returns the current font cap height, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.fontCapHeight()

    def fontLeading(self):
        """
        Returns the current font leading, based on the current `font` and `fontSize`.
        """
        return self._dummyContext._state.text.fontLeading()

    def fontLineHeight(self):
        """
        Returns the current line height, based on the current `font` and `fontSize`.
        If a `lineHeight` is set, this value will be returned.
        """
        return self._dummyContext._state.text.fontLineHeight()

    _bezierPathClass = BezierPath

    def BezierPath(self, path=None, glyphSet=None):
        """
        Return a BezierPath object.
        This is a reusable object, if you want to draw the same over and over again.

        .. downloadcode:: bezierPath.py

            # create a bezier path
            path = BezierPath()

            # move to a point
            path.moveTo((100, 100))
            # line to a point
            path.lineTo((100, 200))
            path.lineTo((200, 200))
            # close the path
            path.closePath()

            # loop over a range of 10
            for i in range(10):
                # set a random color with alpha value of .3
                fill(random(), random(), random(), .3)
                # in each loop draw the path
                drawPath(path)
                # translate the canvas
                translate(5, 5)

            path.text("Hello world", font="Helvetica", fontSize=30, offset=(210, 210))

            print "All Points:"
            print path.points

            print "On Curve Points:"
            print path.onCurvePoints

            print "Off Curve Points:"
            print path.offCurvePoints

            # print out all points from all segments in all contours
            for contour in path.contours:
                for segment in contour:
                    for x, y in segment:
                        print x, y
                print "is open:", contour.open

            # translate the path
            path.translate(0, 300)
            # draw the path again
            drawPath(path)

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

        .. downloadcode:: imageObject.py

            # initiate a new image object
            im = ImageObject()

            # draw in the image
            # the 'with' statement will create a custom context
            # only drawing in the image object
            with im:
                # set a size for the image
                size(200, 200)
                # draw something
                fill(1, 0, 0)
                rect(0, 0, width(), height())
                fill(1)
                fontSize(30)
                text("Hello World", (10, 10))

            # draw in the image in the main context
            image(im, (10, 50))
            # apply some filters
            im.gaussianBlur()

            # get the offset (with a blur this will be negative)
            x, y = im.offset()
            # draw in the image in the main context
            image(im, (300+x, 50+y))

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

        .. downloadcode:: variables.py

            # create small ui element for variables in the script

            Variable([
                # create a variable called 'w'
                # and the related ui is a Slider.
                dict(name="w", ui="Slider"),
                # create a variable called 'h'
                # and the related ui is a Slider.
                dict(name="h", ui="Slider",
                        args=dict(
                            # some vanilla specific
                            # setting for a slider
                            value=100,
                            minValue=50,
                            maxValue=300)),
                # create a variable called 'useColor'
                # and the related ui is a CheckBox.
                dict(name="useColor", ui="CheckBox"),
                # create a variable called 'c'
                # and the related ui is a ColorWell.
                dict(name="c", ui="ColorWell")
                ], globals())

            # draw a rect
            rect(0, 0, w, h)

            # check if the 'useColor' variable is checked
            if useColor:
                # set the fill color from the variables
                fill(c)
            # set the font size
            fontSize(h)
            # draw some text
            text("Hello Variable", (w, h))

        .. downloadcode:: vanillaVariables.py

            # Variable == vanilla power in DrawBot
            from AppKit import NSColor
            # create a color
            _color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .5, 1, .8)
            # setup variables useing different vanilla ui elements.
            Variable([
                dict(name="aList", ui="PopUpButton", args=dict(items=['a', 'b', 'c', 'd'])),
                dict(name="aText", ui="EditText", args=dict(text='hello world')),
                dict(name="aSlider", ui="Slider", args=dict(value=100, minValue=50, maxValue=300)),
                dict(name="aCheckBox", ui="CheckBox", args=dict(value=True)),
                dict(name="aColorWell", ui="ColorWell", args=dict(color=_color)),
                dict(name="aRadioGroup", ui="RadioGroup", args=dict(titles=['I', 'II', 'III'], isVertical=False)),
            ], globals())

            print aList
            print aText
            print aSlider
            print aCheckBox
            print aColorWell
            print aRadioGroup
        """
        document = AppKit.NSDocumentController.sharedDocumentController().currentDocument()
        if not document:
            raise DrawBotError("There is no document open")
        controller = document.vanillaWindowController
        try:
            controller._variableController.buildUI(variables)
            controller._variableController.show()
        except Exception:
            controller._variableController = VariableController(variables, controller.runCode, document)

        data = controller._variableController.get()
        for v, value in data.items():
            workSpace[v] = value


_drawBotDrawingTool = DrawBotDrawingTool()
