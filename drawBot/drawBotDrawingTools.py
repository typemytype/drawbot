import AppKit

import math
import os

from context import getContextForFileExt
from context.baseContext import BezierPath
from context.dummyContext import DummyContext

from misc import DrawBotError, warnings

import math, random

def _getmodulecontents(module, names=None):
    d = {}
    if names is None:
        names = [name for name in dir(module) if not name.startswith("_")]
    for name in names:
        d[name] = getattr(module, name)
    return d

def _deprecatedWarning(txt):
    warnings.warn("lowercase API is deprecated use: '%s'" % txt)

class DrawBotDrawingTool(object):

    def __init__(self):
        self._reset()

    def _get__all__(self):
        return [i for i in dir(self) if not i.startswith("_")]
    
    __all__ = property(_get__all__)

    def _addToNamespace(self, namespace):
        namespace.update(_getmodulecontents(self))
        namespace.update(_getmodulecontents(random, ["random", "randint", "choice"]))
        namespace.update(_getmodulecontents(math))

    def _addInstruction(self, callback, *args, **kwargs):
        self._instructionsStack.append((callback, args, kwargs))

    def _drawInContext(self, context):
        if not self._instructionsStack:
            return
        if self._instructionsStack[0][0] != "newPage":
            self._instructionsStack.insert(0, ("newPage", [self.WIDTH, self.HEIGHT], {}))
        for callback, args, kwargs in self._instructionsStack:
            attr = getattr(context, callback)
            attr(*args, **kwargs)

    def _reset(self):
        self._instructionsStack = []
        self._dummyContext = DummyContext()
        self._width = None
        self._height = None

    ## magic variables

    def _get_width(self):
        if self._width is None:
            return 1000
        return self._width
    
    WIDTH = property(_get_width)

    def _get_height(self):
        if self._height is None:
            return 1000
        return self._height

    HEIGHT = property(_get_height)

    def _get_pageCount(self):
        pageCount = 1
        if self._instructionsStack and self._instructionsStack[0][0] == "newPage":
            pageCount = 0
        for i in self._instructionsStack:
            if i[0] == "newPage":
                pageCount += 1
        return pageCount

    PAGECOUNT = property(_get_pageCount)

    _magicVariables = ["WIDTH", "HEIGHT", "PAGECOUNT"]

    ## public callbacks

    # size and pages

    def size(self, width, height=None):
        """
        Set the width and height of the canvas. 
        Without calling `size` the default drawing board is 1000 by 1000 points.
        
        Afterwards the magic variables `WIDTH` and `HEIGHT` can be used for calculations
        
        .. showcode:: /../examples/size.py
        """
        if height is None:
            width, height = width
        self._width = width
        self._height = height
        self._addInstruction("size", width, height)

    def newPage(self, width=None, height=None):
        """
        Create a new canvas to draw in.
        This will act like a page in a pdf or a frame in a mov.

        Optionally a `width` and `height` argument can be provided to set the size.
        If not provided the default size will be used.

        .. showcode:: /../examples/newPage.py
        """
        self._width = width
        self._height = height
        self._addInstruction("newPage", width, height)

    def newpage(self, width=None, height=None):
        _deprecatedWarning("newPage(%s, %s)" % (width, height))
        self.newPage(width, height)

    def saveImage(self, paths):
        """
        Save or export the canvas to a specified format.
        The argument `paths` can either be a single path or a list of paths.

        The file extension is important because it will determine the format in which the image will be exported.

        All supported file extensions: `pdf`, `svg`, `png`, `jpg`, `jpeg`, `tiff`, `tif`, `gif`, `bmp` and `mov`.
        
        * A `pdf` can be multipage. 
        * A `mov` will use each page as a frame.
        * All images and `svg` formats will only save the current page.

        .. showcode:: /../examples/saveImage.py
        """
        if isinstance(paths, (str, unicode)):
            paths = [paths]
        for path in paths:
            path = os.path.expanduser(path)
            base, ext = os.path.splitext(path)
            ext = ext.lower()[1:]
            context = getContextForFileExt(ext)
            self._drawInContext(context)
            context.saveImage(path)

    def saveimage(self, paths):
        _deprecatedWarning("saveImage()")
        self.saveImage(path)

    # graphic state

    def save(self):
        """
        Save the current state.
        This will save the state of the canvas (with all the transformations)
        but also the state of the colors, strokes...
        """
        self._addInstruction("save")

    def restore(self):
        """
        Restore from a previously saved state.
        This will restore the state of the canvas (with all the transformations)
        but also the state of colors, strokes...
        """
        self._addInstruction("restore")

    # basic shapes

    def rect(self, x, y, w, h):
        """
        Draw a rectangle from position x, y with the given width and height.

        .. showcode:: /../examples/rect.py
        """
        self._addInstruction("rect", x, y, w, h)

    def oval(self, x, y, w, h):
        """
        Draw an oval from position x, y with the given width and height.

        .. showcode:: /../examples/oval.py
        """
        self._addInstruction("oval", x, y, w, h)

    # path

    def newPath(self):
        """
        Create a new path.
        """
        self._addInstruction("newPath")

    def newpath(self):
        _deprecatedWarning("newPath()")
        self.newPath()

    def moveTo(self, (x, y)):
        """
        Move to a point x, y.
        """
        self._addInstruction("moveTo", (x, y))

    def moveto(self, x, y):
        _deprecatedWarning("moveTo((%s, %s))" % (x, y))
        self.moveTo((x, y))

    def lineTo(self, (x, y)):
        """
        Line to a point x, y.
        """
        self._addInstruction("lineTo", (x, y))

    def lineto(self, x, y):
        _deprecatedWarning("lineTo((%s, %s))" % (x, y))
        self.lineTo((x, y))

    def curveTo(self, (x1, y1), (x2, y2), (x3, y3)):
        """
        Curve to a point x3, y3.
        With given bezier handles x1, y1 and x2, y2.
        """
        self._addInstruction("curveTo", (x1, y1), (x2, y2), (x3, y3))

    def curveto(self, x1, y1, x2, y2, x3, y3):
        _deprecatedWarning("curveTo((%s, %s), (%s, %s), (%s, %s))" % (x1, y1, x2, y2, x3, y3))
        self.curveTo((x1, y1), (x2, y2), (x3, y3))
        
    def closePath(self):
        """
        Close the path.
        """
        self._addInstruction("closePath")

    def closepath(self):
        _deprecatedWarning("closePath()")
        self.closePath()

    def drawPath(self, path=None):
        """
        Draw the current path, or draw the provided path.         
        """
        if isinstance(path, AppKit.NSBezierPath):
            path = self._bezierPathClass(path)
        self._addInstruction("drawPath", path)

    def drawpath(self, path=None):
        warning = "drawPath()"
        if path:
            warning = "drawPath(pathObject)"
        _deprecatedWarning(warning)
        self.drawPath(path)

    def clipPath(self, path=None):
        """
        Use the current path as a clipping path.
        The clipping path will used until the canvas get a `restore()`
        """
        self._addInstruction("clipPath", path)

    def clippath(self, path=None):
        _deprecatedWarning("clipPath(path)")
        self.clipPath(path)

    def line(self, x1, y1, x2=None, y2=None):
        """
        Draws a line between two given points.

        .. showcode:: /../examples/line.py
        """
        if x2 is None and y2 is None:
            (x1, y1), (x2, y2) = x1, y1
        else:
            _deprecatedWarning("line((%s, %s), (%s, %s))" % (x1, y1, x2, y2))
        path = self._bezierPathClass()
        path.moveTo((x1, y1))
        path.lineTo((x2, y2))
        self.drawPath(path)

    def polygon(self, x, y=None, *args, **kwargs):
        """
        Draws a polygon with x-amount of points. 
        Optionally a `close` argument can be provided to open or close the path.
        As default a `polygon` is a closed path.

        .. showcode:: /../examples/polygon.py
        """
        isTuple = False
        if isinstance(x, tuple) and isinstance(y, tuple):
            isTuple = True
            args = list(args)
            args.insert(0, y)
            x, y = x
        else:
            _deprecatedWarning("polygon((x, y), (x1, y1), (x2, y2), (x3, y3), ... )")
            args = [args[i:i+2] for i in range(0, len(args), 2)]

        if not args:
            raise DrawBotError, "polygon() expects more then a single point"
        doClose = kwargs.get("close", True)
        if len(kwargs) > 1:
            raise DrawBotError, "unexpected keyword argument for this function"

        path = self._bezierPathClass()
        path.moveTo((x, y))
        for p in args:
            path.lineTo(p)
        if doClose:
            path.closePath()
        self.drawPath(path)

    # color

    def fill(self, r=None, g=None, b=None, alpha=1):
        """
        Sets the fill color with a `red`, `green`, `blue` and alpha` value.
        Each argument must a value float between 0 and 1.

        .. showcode:: /../examples/fill.py
        """
        self._addInstruction("fill", r, g, b, alpha)

    def stroke(self, r=None, g=None, b=None, alpha=1):
        """
        Sets the stroke color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.
        
        .. showcode:: /../examples/stroke.py
        """
        self._addInstruction("stroke", r, g, b, alpha)

    def cmykFill(self, c, m=None, y=None, k=None, alpha=1):
        """
        Set a fill using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK fill color. Each value must be a float between 0.0 and 1.0.

        .. showcode:: /../examples/cmykFill.py
        """
        self._addInstruction("cmykFill", c, m, y, k, alpha)

    def cmykfill(self, c,  m=None, y=None, k=None, alpha=1):
        _deprecatedWarning("cmykFill(%s, %s, %s, %s, alpha=%s)" % (c, m, y, k, alpha))
        self.cmykFill(c, m, y, k)

    def cmykStroke(self, c, m=None, y=None, k=None, alpha=1):
        """
        Set a stroke using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK stroke color. Each value must be a float between 0.0 and 1.0.
        
        .. showcode:: /../examples/cmykStroke.py
        """
        self._addInstruction("cmykStroke", c, m, y, k, alpha)

    def cmykstroke(self, c,  m=None, y=None, k=None, alpha=1):
        _deprecatedWarning("cmykStroke(%s, %s, %s, %s, alpha=%s)" % (c, m, y, k, alpha))
        self.cmykStroke(c, m, y, k)

    def shadow(self, offset, blur=None, color=None):
        """
        Adds a shadow with an `offset` (x, y), `blur` and a `color.
        The `color` argument must be a tuple similary as `fill`
        
        .. showcode:: /../examples/shadow.py
        """
        if color is None:
            color = (0, 0, 0)
        if blur is None:
            blur = 10
        self._addInstruction("shadow", offset, blur, color)

    def cmykShadow(self, offset, blur=None, color=None):
        """
        Adds a cmyk shadow with an `offset` (x, y), `blur` and a `color.
        The `color` argument must be a tuple similary as `cmykFill`
        
        .. showcode:: /../examples/cmykShadow.py
        """
        if color is None:
            color = (0, 0, 0, 1, 1)
        if blur is None:
            blur = 10
        self._addInstruction("cmykShadow", offset, blur, color)

    def cmykshadow(self, offset, blur=None, color=None):
        _deprecatedWarning("cmykShadow(%s,  %s, %s)" % (offset, blur, color))
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
        self._addInstruction("linearGradient", startPoint, endPoint, colors, locations)

    def lineargradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        _deprecatedWarning("linearGradient(%s,  %s, %s, %s)" % (startPoint, endPoint, colors, locations))
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
        self._addInstruction("cmykLinearGradient", startPoint, endPoint, colors, locations)

    def cmyklinearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        _deprecatedWarning("cmykLinearGradient(%s,  %s, %s, %s)" % (startPoint, endPoint, colors, locations))
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
        self._addInstruction("radialGradient", startPoint, endPoint, colors, locations, startRadius, endRadius)

    def radialgradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        _deprecatedWarning("radialGradient(%s,  %s, %s, %s, %s, %s)" % (startPoint, endPoint, colors, locations, startRadius, endRadius))
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
        self._addInstruction("cmykRadialGradient", startPoint, endPoint, colors, locations, startRadius, endRadius)
    
    def cmykradialgradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        _deprecatedWarning("cmykRadialGradient(%s,  %s, %s, %s, %s, %s)" % (startPoint, endPoint, colors, locations, startRadius, endRadius))
        self.cmykRadialGradient(startPoint, endPoint, colors, locations, startRadius, endRadius)

    # path drawing behavoir

    def strokeWidth(self, value):
        """
        Sets stroke width.

        .. showcode:: /../examples/strokeWidth.py
        """
        self._addInstruction("strokeWidth", value)

    def strokewidth(self, value):
        _deprecatedWarning("strokeWidth(%s)" % value)
        self.strokeWidth(value)

    def miterLimit(self, value):
        """
        Set a miter limit. Used on corner points.
        
        .. showcode:: /../examples/miterLimit.py
        """
        self._addInstruction("miterLimit", value)

    def miterlimit(self, value):
        _deprecatedWarning("miterLimit(%s)" % value)
        self.miterLimit(value)

    def lineJoin(self, value):
        """
        Set a line join.

        Possible values are `miter`, `round` and `bevel`.

        .. showcode:: /../examples/lineJoin.py
        """
        self._addInstruction("lineJoin", value)

    def linejoin(self, value):
        _deprecatedWarning("lineJoin(%s)" % value)
        self.lineJoin(value)

    def lineCap(self, value):
        """
        Set a line join.

        Possible values are `butt`, `square` and `round`.

        .. showcode:: /../examples/lineCap.py
        """
        self._addInstruction("lineCap", value)

    def linecap(self, value):
        _deprecatedWarning("lineCap(%s)" % value)
        self.lineCap(value)

    def lineDash(self, *value):
        """
        Set a line dash with any given amount of lenghts. 
        Uneven lenghts will have a visible stroke, uneven lenghts will unvisible.
        
        .. showcode:: /../examples/lineDash.py        
        """
        if not value:
            raise DrawBotError, "lineDash must be a list of dashes or None"
        if isinstance(value[0], (list, tuple)):
            value = value[0]
        self._addInstruction("lineDash", value)

    def linedash(self, *value):
        _deprecatedWarning("lineDash(%s)" % (", ".join(value)))
        self.lineDash(*value)
    
    # transform

    def transform(self, matrix):
        """    
        Transform the canvas with a transformation matrix.
        """
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

        If only 1 argument is provided a proportional skew is applied.
        """
        angle1 = math.radians(angle1)
        angle2 = math.radians(angle2)
        self.transform((1, math.tan(angle2), math.tan(angle1), 1, 0, 0))

    # text

    def font(self, fontName, fontSize=None):
        """
        Set a font with the name of the font.
        Optionally a `fontSize` can be set directly.
        The default font, also used as fallback font, is 'LucidaGrande'.
        The default `fontSize` is 10pt.
        
        The name of the font relates the the font postscript name.

        ::

            font("Times-Italic")
        """
        self._dummyContext.font(fontName, fontSize)
        self._addInstruction("font", fontName, fontSize)

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
        _deprecatedWarning("fontSize(%s)" % fontSize)
        self.fontSize(fontSize)

    def lineHeight(self, value):
        """
        Set the line height.
        """
        self._dummyContext.lineHeight(value)
        self._addInstruction("lineHeight", value)

    def lineheight(self, value):
        _deprecatedWarning("lineHeight(%s)" % value)
        self.lineHeight(value)

    def text(self, txt, x, y=None):
        """
        Draw a text a provided possition.

        .. showcode:: /../examples/text.py 
        """
        if y is None:
            x, y = x
        else:
            warnings.warn("postion must a tuple: text('%s', (%s, %s))" % (txt, x, y))
        w, h = self.textSize(txt, None)
        self.textBox(txt, (x, y, w+1, h))

    def textBox(self, txt, (x, y, w, h), align=None):
        """
        Draw a text a provided rectangle.
        Optionally an alignment can be set. 
        Possible `align` values are: `left`, `center` and `right`.

        If the text overflows the rectangle, the overflowed text is returned.
        
        .. showcode:: /../examples/text.py 
        """
        if align is None:
            align = "left"
        elif align not in self._dummyContext._textAlignMap.keys():
            raise DrawBotError, "align must be %s" % (", ".join(self._dummyContext._textAlignMap.keys()))
        self._addInstruction("textBox", txt, (x, y, w, h), align)
        return self._dummyContext.clippedText(txt, (x, y, w, h), align)

    def textbox(self, txt, x, y, w, h, align=None):
        _deprecatedWarning("textbox(%s, (%s, %s, %s, %s), align=%s)" % (txt, x, y, y, w, align))
        self.textbox(txt, (x, y, w, h), align)

    # images

    def image(self, path, x, y=None, alpha=None):
        """
        Add an image from a `path` with an `offset` and an `alpha` value.
        This should accept most common file types like pdf, jpg, png, tiff and gif.

        Optionally an `alpha` can be provided, which is a value between 0 and 1.
        
        .. showcode:: /../examples/image.py 
        """
        if isinstance(x, (tuple)):
            alpha = y
            x, y = x
        if alpha is None:
            alpha = 1
        self._addInstruction("image", path, (x, y), alpha)

    # mov

    def frameDuration(self, seconds):
        """
        When exporting to `mov` each frame can have duration set in `seconds`.
        """
        self._addInstruction("frameDuration", seconds)

    def frameduration(self, seconds):
        _deprecatedWarning("frameDuration(%s)" % seconds)
        self.frameDuration(seconds)

    # helpers

    def textSize(self, txt, align=None):
        """
        Returns the size of a text with the current settings,
        like `font`, `fontSize` and `lineHeight` as a tuple (width, height).
        """
        return self._dummyContext.textSize(txt, align)

    def textsize(self, txt, align=None):
        _deprecatedWarning("textSize(%s, %s)" % (txt, align))
        return self.textSize(txt, align)

    def installedFonts(self):
        """
        Returns a list of all installed fonts.
        """
        return [str(f) for f in AppKit.NSFontManager.sharedFontManager().availableFonts()]

    def installedfonts(self):
        _deprecatedWarning("installedFonts()")
        return self.installedFonts()

    _bezierPathClass = BezierPath

    def BezierPath(self):
        """
        Return a BezierPath object.
        This is a reusable object, if you want to draw the same over and over again.
        
        All BezierPath methods:

        .. function:: bezierPath.moveTo((x, y))
        .. function:: bezierPath.lineTo((x, y))
        .. function:: bezierPath.curveTo((x1, y1), (x2, y2), (x3, y3))
        .. function:: bezierPath.closePath()
        .. function:: bezierPath.rect(x, y, w, h)
        .. function:: bezierPath.oval(x, y, w, h)
        .. function:: bezierPath.copy()

        .. showcode:: /../examples/bezierPath.py
        """
        return self._bezierPathClass()

    def Bezierpath(self):
        _deprecatedWarning("BezierPath()")
        return self.BezierPath()

_drawBotDrawingTool = DrawBotDrawingTool()
