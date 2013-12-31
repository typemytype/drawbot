import AppKit
import CoreText
import Quartz

from drawBot.misc import DrawBotError, cmyk2rgb, warnings

class BezierPath(object):

    def __init__(self, path=None):
        if path is None:
            self._path = AppKit.NSBezierPath.bezierPath()
        else:
            self._path = path
    
    def __repr__(self):
        return "<BezierPath>"
        
    def moveTo(self, x, y=None):
        """
        Move to a point `x`, `y`.
        """
        if y is None:
            x, y = x
        self._path.moveToPoint_((x, y))

    moveto = moveTo

    def lineTo(self, x, y=None):
        """
        Line to a point `x`, `y`.
        """
        if y is None:
            x, y = x
        self._path.lineToPoint_((x, y))

    lineto = lineTo

    def curveTo(self, x1, y1, x2, y2=None, x3=None, y3=None):
        """
        Curve to a point `x3`, `y3`.
        With given bezier handles `x1`, `y1` and `x2`, `y2`.
        """
        if y2 is None and x3 is None and y3 is None:
            x3, y3 = x2
            x2, y2 = y1
            x1, y1 = x1
        self._path.curveToPoint_controlPoint1_controlPoint2_((x3, y3), (x1, y1), (x2, y2))

    curveto = curveTo

    def arcTo(self, pt1, pt2, radius):
        """
        Arc from one point to an other point with a given `radius`.
        """
        self._path.appendBezierPathWithArcFromPoint_toPoint_radius_(pt1, pt2, radius)

    def closePath(self):
        """
        Close the path.
        """
        self._path.closePath()

    closepath = closePath

    def rect(self, x, y, w, h):
        """
        Add a rectangle at possition `x`, `y` with a size of `w`, `h`
        """
        self._path.appendBezierPathWithRect_(((x, y), (w, h)))

    def oval(self, x, y, w, h):
        """
        Add a oval at possition `x`, `y` with a size of `w`, `h`
        """
        self._path.appendBezierPathWithOvalInRect_(((x, y), (w, h)))

    def getNSBezierPath(self):
        """
        Return the nsBezierPath.
        """
        return self._path

    def setNSBezierPath(self, path):
        """
        Set a nsBezierPath.
        """
        self._path = path
    
    def pointInside(self, (x, y)):
        """
        Check if a point `x`, `y` is inside a path.
        """
        return self._path.containsPoint_((x, y))
    
    def bounds(self):
        """
        Return the bounding box of the path.
        """
        (x, y), (w, h) = self._path.bounds()
        return x, y, w, h

    def controlPointBounds(self):
        """
        Return the bounding box of the path including the offcurve points.
        """
        (x, y), (w, h) = self._path.controlPointBounds()
        return x, y, w, h

    def _points(self, onCurve=True, offCurve=True):
        points = []
        if not onCurve and not offCurve:
            return points
        for index in range(self._path.elementCount()):
            instruction, pts = self._path.elementAtIndex_associatedPoints_(index)
            if not onCurve:
                pts = pts[:-1]
            elif not offCurve:
                pts = pts[-1:]
            points.extend([(p.x, p.y) for p in pts])
        return points
    
    def _get_points(self):
        return self._points()
        
    points = property(_get_points, doc="Return a list of all points.")
    
    def _get_onCurvePoints(self):
        return self._points(offCurve=False)
    
    onCurvePoints = property(_get_onCurvePoints, doc="Return a list of all on curve points.")
    
    def _get_offCurvePoints(self):
        return self._points(onCurve=False)
    
    offCurvePoints = property(_get_offCurvePoints, doc="Return a list of all off curve points.")
    
    def _get_contours(self):
        contours = []
        for index in range(self._path.elementCount()):
            instruction, pts = self._path.elementAtIndex_associatedPoints_(index)
            if instruction == 0:
                contours.append([])
            if pts:
                contours[-1].append([(p.x, p.y) for p in pts])
        if len(contours) >= 2 and len(contours[-1]) == 1 and contours[-1][0] == contours[-2][0]:
            contours.pop()
        return contours

    contours = property(_get_contours, doc="Return a list of contours with all point coordinates sorted in segments.")

    def copy(self):
        """
        Copy the bezier path.
        """
        new = self.__class__()
        new._path = self._path.copy()
        return new

class Color(object):

    def __init__(self, r=None, g=None, b=None, a=1):
        if r is None:
            return
        if isinstance(r, AppKit.NSColor):
            self._color = r.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
        elif g == None and b == None:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, r, r, a)
        elif b == None:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, r, r, g)
        else:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

    def set(self):
        self._color.set()
        
    def setStroke(self):
        self._color.setStroke()
        
    def getNSObject(self):
        return self._color

    def copy(self):
        new = self.__class__()
        new._color = self._color.copy()
        return new

class CMYKColor(Color):

    def __init__(self, c=None, m=None, y=None, k=None, a=1):
        if c is None:
            return
        if isinstance(c, AppKit.NSColor):
            self._color = c.colorUsingColorSpaceName_("NSDeviceCMYKColorSpace")
        else:
            self._color = AppKit.NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, y, k, a)

class Shadow(object):

    _colorClass = Color

    def __init__(self, offset=None, blur=None, color=None):
        if offset is None:
            return
        self.offset = offset
        self.blur = blur
        self.color = self._colorClass(*color)
        self.cmykColor = None

    def copy(self):
        new = self.__class__()
        new.offset = self.offset
        new.blur = self.blur
        new.color = self.color.copy()
        new.cmykColor = None
        if self.cmykColor:
            new.cmykColor = self.cmykColor.copy()
        return new

class Gradient(object):

    _colorClass = Color

    def __init__(self, gradientType=None, start=None, end=None, colors=None, positions=None, startRadius=None, endRadius=None):
        if gradientType is None:
            return
        if gradientType not in ("linear", "radial"):
            raise DrawBotError, "Gradient type must be either line or circle"
        if not colors or len(colors) < 2:
            raise DrawBotError, "Gradient needs at least 2 colors"
        if positions is None:
            positions = [i / float(len(colors)-1) for i in range(len(colors))]
        if len(colors) != len(positions):
            raise DrawBotError, "Gradient needs a correct position for each color"
        self.gradientType = gradientType
        self.colors = [self._colorClass(*color) for color in colors]
        self.cmykColors = None
        self.positions = positions
        self.start = start
        self.end = end
        self.startRadius = startRadius
        self.endRadius = endRadius

    def copy(self):
        new = self.__class__()
        new.gradientType = self.gradientType
        new.colors = [color.copy() for color in self.colors]
        new.cmykColors = None
        if self.cmykColors:
            new.cmykColors = [color.copy() for color in self.cmykColors]
        new.positions = list(self.positions)
        new.start = self.start
        new.end = self.end
        new.startRadius = self.startRadius
        new.endRadius = self.endRadius
        return new

class Text(object):

    def __init__(self):
        self._backupFont = "LucidaGrande"
        self._fontName = self._backupFont
        self._fontSize = 10
        self._lineHeight = None
        self._hyphenation = None
    
    def _get_font(self):
        _font = AppKit.NSFont.fontWithName_size_(self._fontName, self.fontSize)
        if _font == None:
            warnings.warn("font: %s is not installed, back to the fallback font: %s" % (self._fontName, self._backupFont))
            self._fontName = self._backupFont
            _font = AppKit.NSFont.fontWithName_size_(self._backupFont, self.fontSize)
        return _font
            
    font = property(_get_font)
    
    def _get_fontName(self):
        return self._fontName

    def _set_fontName(self, fontName):
        self._fontName = fontName

    fontName = property(_get_fontName, _set_fontName)

    def _get_fontSize(self):
        return self._fontSize
        
    def _set_fontSize(self, value):
        self._fontSize = value
    
    fontSize = property(_get_fontSize, _set_fontSize)

    def _get_lineHeight(self):
        return self._lineHeight

    def _set_lineHeight(self, value):
        self._lineHeight = value

    lineHeight = property(_get_lineHeight, _set_lineHeight)

    def _get_hyphenation(self):
        return self._hyphenation

    def _set_hyphenation(self, value):
        self._hyphenation = value

    hyphenation = property(_get_hyphenation, _set_hyphenation)

    def copy(self):
        new = self.__class__()
        new.fontName = self.fontName
        new.fontSize = self.fontSize
        new.lineHeight = self.lineHeight
        new.hyphenation = self.hyphenation
        return new

class GraphicsState(object):

    _textClass = Text
    _colorClass = Color

    def __init__(self):
        self.fillColor =  self._colorClass(0)
        self.strokeColor = None
        self.cmykFillColor = None
        self.cmykStrokeColor = None
        self.shadow = None
        self.gradient = None
        self.strokeWidth = 1
        self.lineDash = None
        self.lineCap = None
        self.lineJoin = None
        self.miterLimit = 10
        self.text = self._textClass()
        self.path = None

    def copy(self):
        new = self.__class__()
        if self.fillColor is not None:
            new.fillColor = self.fillColor.copy()
        else:
            new.fillColor = None
        if self.strokeColor:
            new.strokeColor = self.strokeColor.copy()
        if self.cmykFillColor:
            new.cmykFillColor = self.cmykFillColor.copy()
        if self.cmykStrokeColor:
            new.cmykStrokeColor = self.cmykStrokeColor.copy()
        if self.shadow:
            new.shadow = self.shadow.copy()
        if self.gradient:
            new.gradient = self.gradient.copy()
        if self.path is not None:
            new.path = self.path.copy()
        new.text = self.text.copy()

        new.strokeWidth = self.strokeWidth
        new.lineCap = self.lineCap
        if self.lineDash is not None:
            new.lineDash = list(self.lineDash)
        new.lineJoin = self.lineJoin
        new.miterLimit = self.miterLimit
        return new

class BaseContext(object):

    _graphicsStateClass = GraphicsState

    _cmykColorClass = CMYKColor
    _colorClass = Color
    _textClass = Text
    _shadowClass = Shadow
    _bezierPathClass = BezierPath
    _gradientClass = Gradient

    fileExtensions = []

    _lineJoinStylesMap = dict(   
        miter=Quartz.kCGLineJoinMiter,
        round=Quartz.kCGLineJoinRound,
        bevel=Quartz.kCGLineJoinBevel
        )

    _lineCapStylesMap = dict(
        butt=Quartz.kCGLineCapButt,
        square=Quartz.kCGLineCapSquare,
        round=Quartz.kCGLineCapRound,
        )

    _textAlignMap = dict(
        center=AppKit.NSCenterTextAlignment,
        left=AppKit.NSLeftTextAlignment,
        right=AppKit.NSRightTextAlignment,
        justified=AppKit.NSJustifiedTextAlignment,
        )

    _softHypen = 0x00AD

    def __init__(self):
        self.width = None
        self.height = None
        self.hasPage = False
        self.reset()

    # overwrite by a subclass

    def _newPage(self, width, height):
        pass

    def _save(self):
        pass

    def _restore(self):
        pass

    def _drawPath(self):
        pass

    def _clipPath(self):
        pass

    def _transform(self, matrix):
        pass

    def _text(self, txt, (x, y)):
        pass

    def _textBox(self, txt, (x, y, w, h), align):
        pass

    def _image(self, path, (x, y), alpha):
        pass

    def _frameDuration(self, seconds):
        pass

    def _reset(self):
        pass

    def _saveImage(self, path):
        pass

    ### 

    def reset(self):
        self._stack = []
        self._state = self._graphicsStateClass()
        self._reset()

    def size(self, width=None, height=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

    def newPage(self, width=None, height=None):
        if self.width is None and width is None:
            raise DrawBotError, "A page must have a width"
        if self.height is None and height is None:
            raise DrawBotError, "A page must have a height"
        self.hasPage = True
        self._newPage(width, height)

    def saveImage(self, path):
        if not self.hasPage:
            raise DrawBotError, "can't save image when no page is set"
        self._saveImage(path)

    def frameDuration(self, seconds):
        self._frameDuration(seconds)

    def save(self):
        self._stack.append(self._state.copy())
        self._save()

    def restore(self):
        if not self._stack:
            raise DrawBotError, "can't restore graphics state: no matching save()"
        self._state = self._stack.pop()
        self._restore()

    def rect(self, x, y, w, h):
        path = self._bezierPathClass()
        path.rect(x, y, w, h)
        self.drawPath(path)

    def oval(self, x, y, w, h):
        path = self._bezierPathClass()
        path.oval(x, y, w, h)
        self.drawPath(path)

    def newPath(self):
        self._state.path = self._bezierPathClass()

    def moveTo(self, pt):
        if self._state.path is None:
            raise DrawBotError, "Create a new path first"
        self._state.path.moveTo(pt)

    def lineTo(self, pt):
        self._state.path.lineTo(pt)

    def curveTo(self, pt1, pt2, pt):
        self._state.path.curveTo(pt1, pt2, pt)
    
    def arcTo(self, pt1, pt2, radius):
        self._state.path.arcTo(pt1, pt2, radius)

    def closePath(self):
        self._state.path.closePath()
    
    def drawPath(self, path):
        if path is not None:
            self._state.path = path
        self._drawPath()

    def clipPath(self, path):
        if path is not None:
            self._state.path = path
        self._clipPath()

    def fill(self, r, g=None, b=None, a=1):
        if r is  None:
            self._state.fillColor = None
            self._state.cmykFillColor = None
            return 
        self._state.fillColor = self._colorClass(r, g, b, a)
        self._state.gradient = None
    
    def cmykFill(self, c , m, y, k, a=1):
        if c is None:
            self.fill(None)
        else:
            self._state.cmykFillColor = self._cmykColorClass(c, m, y, k, a)
            r, g, b = cmyk2rgb(c, m, y, k)
            self.fill(r, g, b, a)

    def stroke(self, r, g=None, b=None, a=1):
        if r is None:
            self._state.strokeColor = None
            self._state.cmykStrokeColor = None
            return
        self._state.strokeColor = self._colorClass(r, g, b, a)
    
    def cmykStroke(self, c , m, y, k, a=1):
        if c is None:
            self.stroke(None)
        else:
            self._state.cmykStrokeColor = self._cmykColorClass(c, m, y, k, a)
            r, g, b = cmyk2rgb(c, m, y, k)
            self.stroke(r, g, b, a)

    def shadow(self, offset, blur, color):
        if offset is None:
            self._state.shadow = None
            return
        self._state.shadow = self._shadowClass(offset, blur, color)

    def cmykShadow(self, offset, blur, color):
        if offset is None:
            self._state.shadow = None
            return
        rgbColor = cmyk2rgb(color[0], color[1], color[2], color[3])
        self._state.shadow = self._shadowClass(offset, blur, rgbColor)
        self._state.shadow.cmykColor = self._cmykColorClass(*color)

    def linearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        if startPoint is None:
            self._state.gradient = None
            return
        self._state.gradient = self._gradientClass("linear", startPoint, endPoint, colors, locations)
        self.fill(None)

    def cmykLinearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        if startPoint is None:
            self._state.gradient = None
            return
        rgbColors = [cmyk2rgb(color[0], color[1], color[2], color[3]) for color in colors]
        self._state.gradient = self._gradientClass("linear", startPoint, endPoint, rgbColors, locations)
        self._state.gradient.cmykColors = [self._cmykColorClass(*color) for color in colors]
        self.fill(None)

    def radialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        if startPoint is None:
            self._state.gradient = None
            return
        self._state.gradient = self._gradientClass("radial", startPoint, endPoint, colors, locations, startRadius, endRadius)
        self.fill(None)

    def cmykRadialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        if startPoint is None:
            self._state.gradient = None
            return
        rgbColors = [cmyk2rgb(color[0], color[1], color[2], color[3]) for color in colors]
        self._state.gradient = self._gradientClass("radial", startPoint, endPoint, rgbColors, locations, startRadius, endRadius)
        self._state.gradient.cmykColors = [self._cmykColorClass(*color) for color in colors]
        self.fill(None)

    def strokeWidth(self, value):
        self._state.strokeWidth = value
    
    def miterLimit(self, value):
        self._state.miterLimit = value
    
    def lineJoin(self, join):
        if join is None:
            self._state.lineJoin = None
        if join not in self._lineJoinStylesMap:
            raise DrawBotError, "lineJoin() argument must be 'bevel', 'miter' or 'round'"
        self._state.lineJoin = self._lineJoinStylesMap[join]
    
    def lineCap(self, cap):
        if cap is None:
            self._state.lineCap = None
        if cap not in self._lineCapStylesMap:
            raise DrawBotError, "lineCap() argument must be 'butt', 'square' or 'round'"
        self._state.lineCap = self._lineCapStylesMap[cap]

    def lineDash(self, dash):
        if dash[0] == None:
            self._state.lineDash = None
            return
        self._state.lineDash = list(dash)

    def transform(self, matrix):
        self._transform(matrix)

    def font(self, fontName, fontSize):
        self._state.text.fontName = fontName
        if fontSize != None:
            self.fontSize(fontSize)
            
    def fontSize(self, fontSize):
        self._state.text.fontSize = fontSize
    
    def lineHeight(self, value):
        self._state.text.lineHeight = value

    def hyphenation(self, value):
        self._state.text.hyphenation = value

    def attributedString(self, txt, align=None):
        attributes = {AppKit.NSFontAttributeName : self._state.text.font}
        if self._state.fillColor is not None:
            extra = {
                AppKit.NSForegroundColorAttributeName : self._state.fillColor.getNSObject(),
                }
            attributes.update(extra)
        if self._state.strokeColor is not None:
            strokeWidth = self._state.strokeWidth
            if self._state.fillColor is not None:
                strokeWidth *= -1
            extra = {
                    AppKit.NSStrokeWidthAttributeName : strokeWidth,
                    AppKit.NSStrokeColorAttributeName : self._state.strokeColor.getNSObject(),
                    }
        
            attributes.update(extra)
        para = AppKit.NSMutableParagraphStyle.alloc().init()
        if align:
            para.setAlignment_(self._textAlignMap[align])
        if self._state.text.lineHeight:
            para.setLineSpacing_(self._state.text.lineHeight)
            para.setMaximumLineHeight_(self._state.text.lineHeight)
            para.setMinimumLineHeight_(self._state.text.lineHeight)
        attributes[AppKit.NSParagraphStyleAttributeName] = para
    
        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(txt, attributes)
        return text

    def hyphenateAttributedString(self, attrString, width):
        attrString = attrString.mutableCopy()
        mutString = attrString.mutableString()
        wordRange = AppKit.NSMakeRange(mutString.length(), 0)
        while wordRange.location > 2:
            wordRange = attrString.doubleClickAtIndex_(wordRange.location - 2)
            hyphenIndex = AppKit.NSMaxRange(wordRange)
            while hyphenIndex != AppKit.NSNotFound:
                hyphenIndex = attrString.lineBreakByHyphenatingBeforeIndex_withinRange_(hyphenIndex, wordRange)
                if hyphenIndex != AppKit.NSNotFound:
                    mutString.insertString_atIndex_(unichr(self._softHypen), hyphenIndex)

        hyphenAttrString = self.attributedString("-")
        hyphenWidth = hyphenAttrString.size().width
        textLength = attrString.length()
        
        setter = CoreText.CTTypesetterCreateWithAttributedString(attrString)
        location = 0

        while location < textLength:
            breakIndex = CoreText.CTTypesetterSuggestLineBreak(setter, location, width)
            sub = attrString.attributedSubstringFromRange_((location, breakIndex))
            location += breakIndex
            subString = sub.string()
            if breakIndex == 0:
                break
            subString = sub.string()
            if subString[-1] == unichr(self._softHypen):
                if sub.size().width + hyphenWidth < width:
                    mutString.insertString_atIndex_("-", location)
                    setter = CoreText.CTTypesetterCreateWithAttributedString(attrString)
                    location += 1
                else:
                    attrString.deleteCharactersInRange_((location-1, 1))
                    setter = CoreText.CTTypesetterCreateWithAttributedString(attrString)
                    location -= breakIndex
                    
        mutString.replaceOccurrencesOfString_withString_options_range_(unichr(self._softHypen), "", AppKit.NSLiteralSearch, (0, mutString.length()))
        return attrString

    def clippedText(self, txt, (x, y, w, h), align):
        attrString = self.attributedString(txt, align=align)
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = CoreText.CGPathCreateMutable()
        CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        visibleRange = CoreText.CTFrameGetVisibleStringRange(box)
        return txt[visibleRange.length:]

    def textSize(self, txt, align):
        text = self.attributedString(txt, align)
        w, h = text.size()
        return w, h

    def textBox(self, txt, (x, y, w, h), align="left"):
        self._state.path = None
        self._textBox(txt, (x, y, w, h), align)

    def image(self, path, (x, y), alpha):
        self._image(path, (x, y), alpha)