import AppKit
import CoreText
import Quartz

import math

from fontTools.pens.basePen import BasePen

from drawBot.misc import DrawBotError, cmyk2rgb, warnings

from tools import openType
from tools import variation


_FALLBACKFONT = "LucidaGrande"


def _tryInstallFontFromFontName(fontName):
    from drawBot.drawBotDrawingTools import _drawBotDrawingTool
    return _drawBotDrawingTool._tryInstallFontFromFontName(fontName)


class BezierContour(list):

    """
    A Bezier contour object.
    """

    def __init__(self, *args, **kwargs):
        super(BezierContour, self).__init__(*args, **kwargs)
        self.open = True

    def __repr__(self):
        return "<BezierContour>"

    def _get_clockwise(self):
        from fontTools.pens.areaPen import AreaPen
        pen = AreaPen()
        pen.endPath = pen.closePath
        self.drawToPen(pen)
        return pen.value < 0

    clockwise = property(_get_clockwise, doc="A boolean representing if the contour has a clockwise direction.")

    def drawToPointPen(self, pointPen):
        pointPen.beginPath()
        for i, segment in enumerate(self):
            if len(segment) == 1:
                segmentType = "line"
                if i == 0 and self.open:
                    segmentType = "move"
                pointPen.addPoint(segment[0], segmentType=segmentType)
            else:
                pointPen.addPoint(segment[0])
                pointPen.addPoint(segment[1])
                pointPen.addPoint(segment[2], segmentType="curve")
        pointPen.endPath()

    def drawToPen(self, pen):
        for i, segment in enumerate(self):
            if i == 0:
                pen.moveTo(*segment)
            elif len(segment) == 1:
                pen.lineTo(*segment)
            else:
                pen.curveTo(*segment)
        if self.open:
            pen.endPath()
        else:
            pen.closePath()

    def _get_points(self):
        return [point for segment in self for point in segment]

    points = property(_get_points, doc="Return a list of all the points making up this contour, regardless of whether they are on curve or off curve.")


class BezierPath(BasePen):

    """
    A bezier path object, if you want to draw the same over and over again.
    """

    contourClass = BezierContour

    _instructionSegmentTypeMap = {
        AppKit.NSMoveToBezierPathElement: "move",
        AppKit.NSLineToBezierPathElement: "line",
        AppKit.NSCurveToBezierPathElement: "curve"
    }

    def __init__(self, path=None, glyphSet=None):
        if path is None:
            self._path = AppKit.NSBezierPath.bezierPath()
        else:
            self._path = path
        BasePen.__init__(self, glyphSet)

    def __repr__(self):
        return "<BezierPath>"

    # pen support

    def _moveTo(self, pt):
        """
        Move to a point `x`, `y`.
        """
        self._path.moveToPoint_(pt)

    def _lineTo(self, pt):
        """
        Line to a point `x`, `y`.
        """
        self._path.lineToPoint_(pt)

    def _curveToOne(self, pt1, pt2, pt3):
        """
        Curve to a point `x3`, `y3`.
        With given bezier handles `x1`, `y1` and `x2`, `y2`.
        """
        self._path.curveToPoint_controlPoint1_controlPoint2_(pt3, pt1, pt2)

    def closePath(self):
        """
        Close the path.
        """
        self._path.closePath()

    def beginPath(self, identifier=None):
        """
        Begin path.
        """
        from ufoLib.pointPen import PointToSegmentPen
        self._pointToSegmentPen = PointToSegmentPen(self)
        self._pointToSegmentPen.beginPath()

    def addPoint(self, *args, **kwargs):
        """
        Add a point to the path.
        """
        self._pointToSegmentPen.addPoint(*args, **kwargs)

    def endPath(self):
        """
        End the path.

        When the bezier path is used as a pen, the path will be open.

        When the bezier path is used as a point pen, the path will process all the points added with `addPoints`.
        """
        if hasattr(self, "_pointToSegmentPen"):
            # its been uses in a point pen world
            self._pointToSegmentPen.endPath()
            del self._pointToSegmentPen

    def drawToPen(self, pen):
        """
        Draw the bezier path into a pen
        """
        contours = self.contours
        for contour in contours:
            contour.drawToPen(pen)

    def drawToPointPen(self, pointPen):
        """
        Draw the bezier path into a point pen.
        """
        contours = self.contours
        for contour in contours:
            contour.drawToPointPen(pointPen)

    def arc(self, center, radius, startAngle, endAngle, clockwise):
        """
        Arc with `center` and a given `radius`, from `startAngle` to `endAngle`, going clockwise if `clockwise` is True and counter clockwise if `clockwise` is False.
        """
        self._path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
            center, radius, startAngle, endAngle, clockwise)

    def arcTo(self, pt1, pt2, radius):
        """
        Arc from one point to an other point with a given `radius`.
        """
        self._path.appendBezierPathWithArcFromPoint_toPoint_radius_(pt1, pt2, radius)

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
        self.closePath()

    def text(self, txt, offset=None, font=_FALLBACKFONT, fontSize=10, align=None):
        """
        Draws a `txt` with a `font` and `fontSize` at an `offset` in the bezier path.
        If a font path is given the font will be installed and used directly.

        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"` and `"right"`.

        The default alignment is `left`.

        Optionally `txt` can be a `FormattedString`.
        """
        if align and align not in BaseContext._textAlignMap.keys():
            raise DrawBotError("align must be %s" % (", ".join(BaseContext._textAlignMap.keys())))
        context = BaseContext()
        context.font(font, fontSize)

        attributedString = context.attributedString(txt, align)
        w, h = attributedString.size()
        if offset:
            x, y = offset
        else:
            x = y = 0
        if align == "right":
            x -= w
        elif align == "center":
            x -= w * .5
        setter = CoreText.CTFramesetterCreateWithAttributedString(attributedString)
        path = Quartz.CGPathCreateMutable()
        Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w, h))
        frame = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CoreText.CTFrameGetLines(frame)
        origins = CoreText.CTFrameGetLineOrigins(frame, (0, len(ctLines)), None)
        if origins:
            y -= origins[0][1]
        self.textBox(txt, box=(x, y - h, w, h * 2), font=font, fontSize=fontSize, align=align)

    def textBox(self, txt, box, font=_FALLBACKFONT, fontSize=10, align=None, hyphenation=None):
        """
        Draws a `txt` with a `font` and `fontSize` in a `box` in the bezier path.
        If a font path is given the font will be installed and used directly.

        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"` and `"right"`.

        The default alignment is `left`.

        Optionally `hyphenation` can be provided.

        Optionally `txt` can be a `FormattedString`.
        Optionally `box` can be a `BezierPath`.
        """
        if align and align not in BaseContext._textAlignMap.keys():
            raise DrawBotError("align must be %s" % (", ".join(BaseContext._textAlignMap.keys())))
        context = BaseContext()
        context.font(font, fontSize)
        context.hyphenation(hyphenation)

        path, (x, y) = context._getPathForFrameSetter(box)
        attributedString = context.attributedString(txt, align)

        setter = CoreText.CTFramesetterCreateWithAttributedString(attributedString)
        frame = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CoreText.CTFrameGetLines(frame)
        origins = CoreText.CTFrameGetLineOrigins(frame, (0, len(ctLines)), None)

        for i, (originX, originY) in enumerate(origins):
            ctLine = ctLines[i]
            ctRuns = CoreText.CTLineGetGlyphRuns(ctLine)
            for ctRun in ctRuns:
                attributes = CoreText.CTRunGetAttributes(ctRun)
                font = attributes.get(AppKit.NSFontAttributeName)
                baselineShift = attributes.get(AppKit.NSBaselineOffsetAttributeName, 0)
                glyphCount = CoreText.CTRunGetGlyphCount(ctRun)
                for i in range(glyphCount):
                    glyph = CoreText.CTRunGetGlyphs(ctRun, (i, 1), None)[0]
                    ax, ay = CoreText.CTRunGetPositions(ctRun, (i, 1), None)[0]
                    if glyph:
                        self._path.moveToPoint_((x + originX + ax, y + originY + ay + baselineShift))
                        self._path.appendBezierPathWithGlyph_inFont_(glyph, font)
        self.optimizePath()
        return context.clippedText(txt, box, align)

    def traceImage(self, path, threshold=.2, blur=None, invert=False, turd=2, tolerance=0.2, offset=None):
        """
        Convert a given image to a vector outline.

        Optionally some tracing options can be provide:

        * `threshold`: the threshold used to bitmap an image
        * `blur`: the image can be blurred
        * `invert`: invert to the image
        * `turd`: the size of small turd that can be ignored
        * `tolerance`: the precision tolerance of the vector outline
        * `offset`: add the traced vector outline with an offset to the BezierPath
        """
        from tools import traceImage
        traceImage.TraceImage(path, self, threshold, blur, invert, turd, tolerance, offset)

    def getNSBezierPath(self):
        """
        Return the nsBezierPath.
        """
        return self._path

    def _getCGPath(self):
        path = Quartz.CGPathCreateMutable()
        count = self._path.elementCount()
        for i in range(count):
            instruction, points = self._path.elementAtIndex_associatedPoints_(i)
            if instruction == AppKit.NSMoveToBezierPathElement:
                Quartz.CGPathMoveToPoint(path, None, points[0].x, points[0].y)
            elif instruction == AppKit.NSLineToBezierPathElement:
                Quartz.CGPathAddLineToPoint(path, None, points[0].x, points[0].y)
            elif instruction == AppKit.NSCurveToBezierPathElement:
                Quartz.CGPathAddCurveToPoint(
                    path, None,
                    points[0].x, points[0].y,
                    points[1].x, points[1].y,
                    points[2].x, points[2].y
                )
            elif instruction == AppKit.NSClosePathBezierPathElement:
                Quartz.CGPathCloseSubpath(path)
        # hacking to get a proper close path at the end of the path
        x, y, _, _ = self.bounds()
        Quartz.CGPathMoveToPoint(path, None, x, y)
        Quartz.CGPathAddLineToPoint(path, None, x, y)
        Quartz.CGPathAddLineToPoint(path, None, x, y)
        Quartz.CGPathAddLineToPoint(path, None, x, y)
        Quartz.CGPathCloseSubpath(path)
        return path

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
        if self._path.isEmpty():
            return None
        (x, y), (w, h) = self._path.bounds()
        return x, y, x + w, y + h

    def controlPointBounds(self):
        """
        Return the bounding box of the path including the offcurve points.
        """
        (x, y), (w, h) = self._path.controlPointBounds()
        return x, y, x + w, y + h

    def optimizePath(self):
        count = self._path.elementCount()
        if self._path.elementAtIndex_(count - 1) == AppKit.NSMoveToBezierPathElement:
            optimizedPath = AppKit.NSBezierPath.bezierPath()
            for i in range(count - 1):
                instruction, points = self._path.elementAtIndex_associatedPoints_(i)
                if instruction == AppKit.NSMoveToBezierPathElement:
                    optimizedPath.moveToPoint_(*points)
                elif instruction == AppKit.NSLineToBezierPathElement:
                    optimizedPath.lineToPoint_(*points)
                elif instruction == AppKit.NSCurveToBezierPathElement:
                    p1, p2, p3 = points
                    optimizedPath.curveToPoint_controlPoint1_controlPoint2_(p3, p1, p2)
                elif instruction == AppKit.NSClosePathBezierPathElement:
                    optimizedPath.closePath()
            self._path = optimizedPath

    def copy(self):
        """
        Copy the bezier path.
        """
        new = self.__class__()
        new._path = self._path.copy()
        return new

    def reverse(self):
        """
        Reverse the path direction
        """
        self._path = self._path.bezierPathByReversingPath()

    def appendPath(self, otherPath):
        """
        Append a path.
        """
        self._path.appendBezierPath_(otherPath.getNSBezierPath())

    def __add__(self, otherPath):
        new = self.copy()
        new.appendPath(otherPath)
        return new

    def __iadd__(self, other):
        self.appendPath(other)
        return self

    # transformations

    def translate(self, x=0, y=0):
        """
        Translate the path with a given offset.
        """
        self.transform((1, 0, 0, 1, x, y))

    def rotate(self, angle):
        """
        Rotate the path around the origin point with a given angle in degrees.
        """
        angle = math.radians(angle)
        c = math.cos(angle)
        s = math.sin(angle)
        self.transform((c, s, -s, c, 0, 0))

    def scale(self, x=1, y=None):
        """
        Scale the path with a given `x` (horizontal scale) and `y` (vertical scale).

        If only 1 argument is provided a proportional scale is applied.
        """
        if y is None:
            y = x
        self.transform((x, 0, 0, y, 0, 0))

    def skew(self, angle1, angle2=0):
        """
        Skew the path with given `angle1` and `angle2`.

        If only one argument is provided a proportional skew is applied.
        """
        angle1 = math.radians(angle1)
        angle2 = math.radians(angle2)
        self.transform((1, math.tan(angle2), math.tan(angle1), 1, 0, 0))

    def transform(self, transformMatrix):
        """
        Transform a path with a transform matrix (xy, xx, yy, yx, x, y).
        """
        aT = AppKit.NSAffineTransform.transform()
        aT.setTransformStruct_(transformMatrix[:])
        self._path.transformUsingAffineTransform_(aT)

    # boolean operations

    def _contoursForBooleanOperations(self):
        # contours are very temporaly objects
        # redirect drawToPointPen to drawPoints
        contours = self.contours
        for contour in contours:
            contour.drawPoints = contour.drawToPointPen
        return contours

    def union(self, other):
        """
        Return the union between two bezier paths.
        """
        import booleanOperations
        contours = self._contoursForBooleanOperations() + other._contoursForBooleanOperations()
        result = self.__class__()
        booleanOperations.union(contours, result)
        return result

    def removeOverlap(self):
        """
        Remove all overlaps in a bezier path.
        """
        import booleanOperations
        contours = self._contoursForBooleanOperations()
        result = self.__class__()
        booleanOperations.union(contours, result)
        self.setNSBezierPath(result.getNSBezierPath())
        return self

    def difference(self, other):
        """
        Return the difference between two bezier paths.
        """
        import booleanOperations
        subjectContours = self._contoursForBooleanOperations()
        clipContours = other._contoursForBooleanOperations()
        result = self.__class__()
        booleanOperations.difference(subjectContours, clipContours, result)
        return result

    def intersection(self, other):
        """
        Return the intersection between two bezier paths.
        """
        import booleanOperations
        subjectContours = self._contoursForBooleanOperations()
        clipContours = other._contoursForBooleanOperations()
        result = self.__class__()
        booleanOperations.intersection(subjectContours, clipContours, result)
        return result

    def xor(self, other):
        """
        Return the xor between two bezier paths.
        """
        import booleanOperations
        subjectContours = self._contoursForBooleanOperations()
        clipContours = other._contoursForBooleanOperations()
        result = self.__class__()
        booleanOperations.xor(subjectContours, clipContours, result)
        return result

    def __mod__(self, other):
        return self.difference(other)

    __rmod__ = __mod__

    def __imod__(self, other):
        result = self.difference(other)
        self.setNSBezierPath(result.getNSBezierPath())
        return self

    def __or__(self, other):
        return self.union(other)

    __ror__ = __or__

    def __ior__(self, other):
        result = self.union(other)
        self.setNSBezierPath(result.getNSBezierPath())
        return self

    def __and__(self, other):
        return self.intersection(other)

    __rand__ = __and__

    def __iand__(self, other):
        result = self.intersection(other)
        self.setNSBezierPath(result.getNSBezierPath())
        return self

    def __xor__(self, other):
        return self.xor(other)

    __rxor__ = __xor__

    def __ixor__(self, other):
        result = self.xor(other)
        self.setNSBezierPath(result.getNSBezierPath())
        return self

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
            if instruction == AppKit.NSMoveToBezierPathElement:
                contours.append(self.contourClass())
            if instruction == AppKit.NSClosePathBezierPathElement:
                contours[-1].open = False
            if pts:
                contours[-1].append([(p.x, p.y) for p in pts])
        if len(contours) >= 2 and len(contours[-1]) == 1 and contours[-1][0] == contours[-2][0]:
            contours.pop()
        return contours

    contours = property(_get_contours, doc="Return a list of contours with all point coordinates sorted in segments. A contour object has an `open` attribute.")

    def __len__(self):
        return len(self.contours)

    def __getitem__(self, index):
        return self.contours[index]

    def __iter__(self):
        contours = self.contours
        count = len(contours)
        index = 0
        while index < count:
            contour = contours[index]
            yield contour
            index += 1


class Color(object):

    colorSpace = AppKit.NSColorSpace.genericRGBColorSpace

    def __init__(self, r=None, g=None, b=None, a=1):
        self._color = None
        if r is None:
            return
        if isinstance(r, AppKit.NSColor):
            self._color = r
        elif g is None and b is None:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, r, r, a)
        elif b is None:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, r, r, g)
        else:
            self._color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)
        self._color = self._color.colorUsingColorSpace_(self.colorSpace())

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

    @classmethod
    def getColorsFromList(self, inputColors):
        outputColors = []
        for color in inputColors:
            color = self.getColor(color)
            outputColors.append(color)
        return outputColors

    @classmethod
    def getColor(self, color):
        if isinstance(color, self.__class__):
            return color
        elif isinstance(color, (tuple, list)):
            return self(*color)
        elif isinstance(color, AppKit.NSColor):
            return self(color)
        raise DrawBotError("Not a valid color: %s" % color)


class CMYKColor(Color):

    colorSpace = AppKit.NSColorSpace.genericCMYKColorSpace

    def __init__(self, c=None, m=None, y=None, k=None, a=1):
        if c is None:
            return
        if isinstance(c, AppKit.NSColor):
            self._color = c
        else:
            self._color = AppKit.NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, y, k, a)
        self._color = self._color.colorUsingColorSpace_(self.colorSpace())
        self._cmyka = c, m, y, k, a


class Shadow(object):

    _colorClass = Color

    def __init__(self, offset=None, blur=None, color=None):
        if offset is None:
            return
        self.offset = offset
        self.blur = blur
        self.color = self._colorClass.getColor(color)
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
            raise DrawBotError("Gradient type must be either 'linear' or 'radial'")
        if not colors or len(colors) < 2:
            raise DrawBotError("Gradient needs at least 2 colors")
        if positions is None:
            positions = [i / float(len(colors) - 1) for i in range(len(colors))]
        if len(colors) != len(positions):
            raise DrawBotError("Gradient needs a correct position for each color")
        self.gradientType = gradientType
        self.colors = self._colorClass.getColorsFromList(colors)
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


class FormattedString(object):

    """
    FormattedString is a reusable object, if you want to draw the same over and over again.
    FormattedString objects can be drawn with the `text(txt, (x, y))` and `textBox(txt, (x, y, w, h))` methods.
    """

    _colorClass = Color
    _cmykColorClass = CMYKColor

    _textAlignMap = dict(
        center=AppKit.NSCenterTextAlignment,
        left=AppKit.NSLeftTextAlignment,
        right=AppKit.NSRightTextAlignment,
        justified=AppKit.NSJustifiedTextAlignment,
    )

    _textTabAlignMap = dict(
        center=AppKit.NSCenterTextAlignment,
        left=AppKit.NSLeftTextAlignment,
        right=AppKit.NSRightTextAlignment,
    )

    _textUnderlineMap = dict(
        single=AppKit.NSUnderlineStyleSingle,
        # thick=AppKit.NSUnderlineStyleThick,
        # double=AppKit.NSUnderlineStyleDouble,
        # solid=AppKit.NSUnderlinePatternSolid,
        # dotted=AppKit.NSUnderlinePatternDot,
        # dashed=AppKit.NSUnderlinePatternDash,
        # dotDashed=AppKit.NSUnderlinePatternDashDot,
        # dotDotted=AppKit.NSUnderlinePatternDashDotDot,
        # byWord=0x8000 # AppKit.NSUnderlineByWord,
    )

    _formattedAttributes = dict(
        font=_FALLBACKFONT,
        fallbackFont=None,
        fontSize=10,

        fill=(0, 0, 0),
        cmykFill=None,
        stroke=None,
        cmykStroke=None,
        strokeWidth=1,

        align=None,
        lineHeight=None,
        tracking=None,
        baselineShift=None,
        underline=None,
        openTypeFeatures=dict(),
        fontVariations=dict(),
        tabs=None,
        indent=None,
        tailIndent=None,
        firstLineIndent=None,
        paragraphTopSpacing=None,
        paragraphBottomSpacing=None,

        language=None,
    )

    def __init__(self, txt=None, **kwargs):
        self.clear()
        # create all _<attributes> in the formatted text object
        # with default values
        for key, value in self._formattedAttributes.items():
            setattr(self, "_%s" % key, value)
        attributes = self._validateAttributes(kwargs, addDefaults=False)
        if txt:
            self.append(txt, **attributes)
        else:
            # call each method with the provided value
            for key, value in attributes.items():
                self._setAttribute(key, value)
            self._setColorAttributes(attributes)

    def _setAttribute(self, attribute, value):
        method = getattr(self, attribute)
        if isinstance(value, (list, tuple)):
            method(*value)
        elif isinstance(value, dict):
            method(**value)
        else:
            method(value)

    def _setColorAttributes(self, attributes):
        colorAttributeNames = ("fill", "stroke", "cmykFill", "cmykStroke")
        for key in colorAttributeNames:
            value = attributes.get(key)
            if value is not None:
                setattr(self, "_%s" % key, value)

        if self._fill is not None:
            try:
                len(self._fill)
            except Exception:
                self._fill = (self._fill,)
        if self._stroke is not None:
            try:
                len(self._stroke)
            except Exception:
                self._stroke = (self._stroke,)
        if self._fill:
            self._cmykFill = None
        elif self._cmykFill:
            self._fill = None

        if self._stroke:
            self._cmykStroke = None
        elif self._cmykStroke:
            self._stroke = None

    def _validateAttributes(self, attributes, addDefaults=True):
        for attribute in attributes:
            if attribute not in self._formattedAttributes:
                raise TypeError("FormattedString got an unexpected keyword argument '%s'" % attribute)
        result = dict()
        if addDefaults:
            for key, value in self._formattedAttributes.items():
                if isinstance(value, dict):
                    value = dict(value)
                elif isinstance(value, list):
                    value = list(value)
                result[key] = value
        result.update(attributes)
        return result

    def clear(self):
        self._attributedString = AppKit.NSMutableAttributedString.alloc().init()

    def append(self, txt, **kwargs):
        """
        Add `txt` to the formatted string with some additional text formatting attributes:

        * `font`: the font to be used for the given text, if a font path is given the font will be installed and used directly.
        * `fallbackFont`: the fallback font
        * `fontSize`: the font size to be used for the given text
        * `fill`: the fill color to be used for the given text
        * `cmykFill`: the cmyk fill color to be used for the given text
        * `stroke`: the stroke color to be used for the given text
        * `cmykStroke`: the cmyk stroke color to be used for the given text
        * `strokeWidth`: the strokeWidth to be used for the given text
        * `align`: the alignment to be used for the given text
        * `lineHeight`: the lineHeight to be used for the given text
        * `tracking`: set tracking for the given text
        * `baselineShift`: set base line shift for the given text
        * `openTypeFeatures`: enable OpenType features
        * `fontVariations`: pick a variation by axes values
        * `tabs`: enable tabs
        * `indent`: the indent of a paragraph
        * `tailIndent`: the tail indent of a paragraph
        * `firstLineIndent`: the first line indent of a paragraph
        * `paragraphTopSpacing`: the spacing at the top of a paragraph
        * `paragraphBottomSpacing`: the spacing at the bottom of a paragraph
        * `language`: the language of the text

        All formatting attributes follow the same notation as other similar DrawBot methods.
        A color is a tuple of `(r, g, b, alpha)`, and a cmykColor is a tuple of `(c, m, y, k, alpha)`.

        Text can also be added with `formattedString += "hello"`. It will append the text with the current settings of the formatted string.
        """
        if isinstance(txt, (str, unicode)):
            try:
                txt = txt.decode("utf-8")
            except UnicodeEncodeError:
                pass
        attributes = self._validateAttributes(kwargs, addDefaults=False)
        for key, value in attributes.items():
            self._setAttribute(key, value)
        self._setColorAttributes(attributes)

        if isinstance(txt, FormattedString):
            self._attributedString.appendAttributedString_(txt.getNSObject())
            return
        attributes = {}
        if self._font:
            font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
            if font is None:
                ff = self._fallbackFont
                if ff is None:
                    ff = _FALLBACKFONT
                warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, ff))
                font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
            coreTextfeatures = []
            if self._openTypeFeatures:
                existingOpenTypeFeatures = openType.getFeatureTagsForFontName(self._font)
                # sort features by their on/off state
                # set all disabled features first
                orderedOpenTypeFeatures = sorted(self._openTypeFeatures.items(), key=lambda (k, v): v)
                for featureTag, value in orderedOpenTypeFeatures:
                    coreTextFeatureTag = featureTag
                    if not value:
                        coreTextFeatureTag = "%s_off" % featureTag
                    if coreTextFeatureTag in openType.featureMap:
                        if value and featureTag not in existingOpenTypeFeatures:
                            # only warn when the feature is on and not existing for the current font
                            warnings.warn("OpenType feature '%s' not available for '%s'" % (featureTag, self._font))
                        feature = openType.featureMap[coreTextFeatureTag]
                        coreTextfeatures.append(feature)
                    else:
                        warnings.warn("OpenType feature '%s' not available" % (featureTag))
            coreTextFontVariations = dict()
            if self._fontVariations:
                existingAxes = variation.getVariationAxesForFontName(self._font)
                for axis, value in self._fontVariations.items():
                    if axis in existingAxes:
                        existinsAxis = existingAxes[axis]
                        # clip variation value within the min max value
                        if value < existinsAxis["minValue"]:
                            value = existinsAxis["minValue"]
                        if value > existinsAxis["maxValue"]:
                            value = existinsAxis["maxValue"]
                        coreTextFontVariations[variation.convertVariationTagToInt(axis)] = value
                    else:
                        warnings.warn("variation axis '%s' not available for '%s'" % (axis, self._font))
            fontAttributes = {}
            if coreTextfeatures:
                fontAttributes[CoreText.NSFontFeatureSettingsAttribute] = coreTextfeatures
            if coreTextFontVariations:
                fontAttributes[CoreText.NSFontVariationAttribute] = coreTextFontVariations
            if self._fallbackFont:
                fontAttributes[CoreText.NSFontCascadeListAttribute] = [AppKit.NSFontDescriptor.fontDescriptorWithName_size_(self._fallbackFont, self._fontSize)]
            fontDescriptor = font.fontDescriptor()
            fontDescriptor = fontDescriptor.fontDescriptorByAddingAttributes_(fontAttributes)
            font = AppKit.NSFont.fontWithDescriptor_size_(fontDescriptor, self._fontSize)
            attributes[AppKit.NSFontAttributeName] = font
        elif self._fontSize:
            font = AppKit.NSFont.fontWithName_size_(_FALLBACKFONT, self._fontSize)
            attributes[AppKit.NSFontAttributeName] = font
        if self._fill or self._cmykFill:
            if self._fill:
                fillColor = self._colorClass.getColor(self._fill).getNSObject()
            elif self._cmykFill:
                fillColor = self._cmykColorClass.getColor(self._cmykFill).getNSObject()
            attributes[AppKit.NSForegroundColorAttributeName] = fillColor
        else:
            # seems like the default foreground color is black
            # set clear color when the fill is None
            attributes[AppKit.NSForegroundColorAttributeName] = AppKit.NSColor.clearColor()
        if self._stroke or self._cmykStroke:
            if self._stroke:
                strokeColor = self._colorClass.getColor(self._stroke).getNSObject()
            elif self._cmykStroke:
                strokeColor = self._cmykColorClass.getColor(self._cmykStroke).getNSObject()
            attributes[AppKit.NSStrokeColorAttributeName] = strokeColor
            attributes[AppKit.NSStrokeWidthAttributeName] = -abs(self._strokeWidth)
        para = AppKit.NSMutableParagraphStyle.alloc().init()
        if self._align:
            para.setAlignment_(self._textAlignMap[self._align])
        if self._tabs:
            for tabStop in para.tabStops():
                para.removeTabStop_(tabStop)
            for tab, tabAlign in self._tabs:
                tabOptions = None
                if tabAlign in self._textTabAlignMap:
                    tabAlign = self._textTabAlignMap[tabAlign]
                else:
                    tabCharSet = AppKit.NSCharacterSet.characterSetWithCharactersInString_(tabAlign)
                    tabOptions = {AppKit.NSTabColumnTerminatorsAttributeName: tabCharSet}
                    tabAlign = self._textAlignMap["right"]
                tabStop = AppKit.NSTextTab.alloc().initWithTextAlignment_location_options_(tabAlign, tab, tabOptions)
                para.addTabStop_(tabStop)
        if self._lineHeight is not None:
            # para.setLineSpacing_(lineHeight)
            para.setMaximumLineHeight_(self._lineHeight)
            para.setMinimumLineHeight_(self._lineHeight)

        if self._indent is not None:
            para.setHeadIndent_(self._indent)
            para.setFirstLineHeadIndent_(self._indent)
        if self._tailIndent is not None:
            para.setTailIndent_(self._tailIndent)
        if self._firstLineIndent is not None:
            para.setFirstLineHeadIndent_(self._firstLineIndent)

        if self._paragraphTopSpacing is not None:
            para.setParagraphSpacingBefore_(self._paragraphTopSpacing)
        if self._paragraphBottomSpacing is not None:
            para.setParagraphSpacing_(self._paragraphBottomSpacing)

        if self._tracking:
            attributes[AppKit.NSKernAttributeName] = self._tracking
        if self._baselineShift is not None:
            attributes[AppKit.NSBaselineOffsetAttributeName] = self._baselineShift
        if self._underline in self._textUnderlineMap:
            attributes[AppKit.NSUnderlineStyleAttributeName] = self._textUnderlineMap[self._underline]
        if self._language:
            attributes["NSLanguage"] = self._language
        attributes[AppKit.NSParagraphStyleAttributeName] = para
        txt = AppKit.NSAttributedString.alloc().initWithString_attributes_(txt, attributes)
        self._attributedString.appendAttributedString_(txt)

    def __add__(self, txt):
        new = self.copy()
        if isinstance(txt, self.__class__):
            new.getNSObject().appendAttributedString_(txt.getNSObject())
        else:
            if not isinstance(txt, (str, unicode)):
                raise TypeError("FormattedString requires a str or unicode, got '%s'" % type(txt))
            new.append(txt)
        return new

    def __getitem__(self, index):
        if isinstance(index, slice):
            start = index.start
            stop = index.stop
            textLength = len(self)

            if start is None:
                start = 0
            elif start < 0:
                start = textLength + start
            elif start > textLength:
                start = textLength

            if stop is None:
                stop = textLength
            elif stop < 0:
                stop = textLength + stop

            if start + (stop - start) > textLength:
                stop = textLength

            location = start
            length = stop - start

            if location < 0:
                location = 0
            if length > textLength:
                length = textLength
            elif length < 0:
                length = 0

            rng = location, length
            attributes = {key: getattr(self, "_%s" % key) for key in self._formattedAttributes}
            new = self.__class__(**attributes)
            try:
                new._attributedString = self._attributedString.attributedSubstringFromRange_(rng)
            except Exception:
                pass
            return new
        else:
            text = self._attributedString.string()
            return text[index]

    def __len__(self):
        return self._attributedString.length()

    def __repr__(self):
        return self._attributedString.string()

    def font(self, font, fontSize=None):
        """
        Set a font with the name of the font.
        If a font path is given the font will be installed and used directly.
        Optionally a `fontSize` can be set directly.
        The default font, also used as fallback font, is 'LucidaGrande'.
        The default `fontSize` is 10pt.

        The name of the font relates to the font's postscript name.

        The font name is returned, which is handy when the font was loaded
        from a path.
        """
        font = _tryInstallFontFromFontName(font)
        font = font.encode("ascii", "ignore")
        self._font = font
        if fontSize is not None:
            self._fontSize = fontSize
        return font

    def fallbackFont(self, font):
        """
        Set a fallback font, used whenever a glyph is not available in the normal font.
        If a font path is given the font will be installed and used directly.
        """
        if font:
            font = _tryInstallFontFromFontName(font)
            font = font.encode("ascii", "ignore")
            testFont = AppKit.NSFont.fontWithName_size_(font, self._fontSize)
            if testFont is None:
                raise DrawBotError("Fallback font '%s' is not available" % font)
        self._fallbackFont = font
        return font

    def fontSize(self, fontSize):
        """
        Set the font size in points.
        The default `fontSize` is 10pt.
        """
        self._fontSize = fontSize

    def fill(self, *fill):
        """
        Sets the fill color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.
        """
        if fill and fill[0] is None:
            fill = None
        self._fill = fill
        self._cmykFill = None

    def stroke(self, *stroke):
        """
        Sets the stroke color with a `red`, `green`, `blue` and `alpha` value.
        Each argument must a value float between 0 and 1.
        """
        if stroke and stroke[0] is None:
            stroke = None
        self._stroke = stroke
        self._cmykStroke = None

    def cmykFill(self, *cmykFill):
        """
        Set a fill using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK fill color. Each value must be a float between 0.0 and 1.0.
        """
        if cmykFill and cmykFill[0] is None:
            cmykFill = None
        self._cmykFill = cmykFill
        self._fill = None

    def cmykStroke(self, *cmykStroke):
        """
        Set a stroke using a CMYK color before drawing a shape. This is handy if the file is intended for print.

        Sets the CMYK stroke color. Each value must be a float between 0.0 and 1.0.
        """
        if cmykStroke and cmykStroke[0] is None:
            cmykStroke = None
        self._cmykStroke = cmykStroke
        self._stroke = None

    def strokeWidth(self, strokeWidth):
        """
        Sets stroke width.
        """
        self._strokeWidth = strokeWidth

    def align(self, align):
        """
        Sets the text alignment.
        Possible `align` values are: `left`, `center` and `right`.
        """
        self._align = align

    def lineHeight(self, lineHeight):
        """
        Set the line height.
        """
        self._lineHeight = lineHeight

    def tracking(self, tracking):
        """
        Set the tracking between characters.
        """
        self._tracking = tracking

    def baselineShift(self, baselineShift):
        """
        Set the shift of the baseline.
        """
        self._baselineShift = baselineShift

    def underline(self, underline):
        """
        Set the underline value.
        Underline must be `single` or `None`.
        """
        self._underline = underline

    def openTypeFeatures(self, *args, **features):
        """
        Enable OpenType features.

        .. downloadcode:: openTypeFeaturesFormattedString.py

            # create an empty formatted string object
            t = FormattedString()
            # set a font
            t.font("ACaslonPro-Regular")
            # set a font size
            t.fontSize(60)
            # add some text
            t += "0123456789 Hello"
            # enable some open type features
            t.openTypeFeatures(smcp=True, lnum=True)
            # add some text
            t += " 0123456789 Hello"
            # draw the formatted string
            text(t, (10, 100))
        """
        if args and args[0] is None:
            self._openTypeFeatures.clear()
        else:
            self._openTypeFeatures.update(features)

    def listOpenTypeFeatures(self, fontName=None):
        """
        List all OpenType feature tags for the current font.

        Optionally a `fontName` can be given. If a font path is given the font will be installed and used directly.
        """
        if fontName:
            fontName = _tryInstallFontFromFontName(fontName)
        else:
            fontName = self._font
        return openType.getFeatureTagsForFontName(fontName)

    def fontVariations(self, *args, **axes):
        """
        Pick a variation by axes values.
        """
        if args and args[0] is None:
            self._fontVariations.clear()
        else:
            self._fontVariations.update(axes)

    def listFontVariations(self, fontName):
        """
        List all variation axes for the current font.

        Optionally a `fontName` can be given. If a font path is given the font will be installed and used directly.
        """
        if fontName:
            fontName = _tryInstallFontFromFontName(fontName)
        else:
            fontName = self._font
        return variation.getVariationAxesForFontName(fontName)

    def tabs(self, *tabs):
        """
        Set tabs,tuples of (`float`, `alignment`)
        Aligment can be `"left"`, `"center"`, `"right"` or any other character.
        If a character is provided the alignment will be `right` and centered on the specified character.

        .. downloadcode:: tabsFormattedString.py

            # create a new formatted string
            t = FormattedString()
            # set some tabs
            t.tabs((85, "center"), (232, "right"), (300, "left"))
            # add text with tabs
            t += " hello w o r l d".replace(" ", "\\t")
            # draw the string
            text(t, (10, 10))
        """
        if tabs and tabs[0] is None:
            self._tabs = None
        else:
            self._tabs = tabs

    def indent(self, indent):
        """
        Set indent of text left of the paragraph.

        .. downloadcode:: indent.py

            # setting up some variables
            x, y, w, h = 10, 10, 200, 300

            txtIndent = 50
            txtFirstLineIndent = 70
            txtTailIndent = -50

            paragraphTop = 3
            paragraphBottom = 10

            txt = '''DrawBot is an ideal tool to teach the basics of programming. Students get colorful graphic treats while getting familiar with variables, conditional statements, functions and what have you. Results can be saved in a selection of different file formats, including as high resolution, scaleable PDF, svg, movie, png, jpeg, tiff...'''

            # a new page with preset size
            newPage(w+x*2, h+y*2)
            # draw text indent line
            stroke(1, 0, 0)
            line((x+txtIndent, y), (x+txtIndent, y+h))
            # draw text firstline indent line
            stroke(1, 1, 0)
            line((x+txtFirstLineIndent, y), (x+txtFirstLineIndent, y+h))
            # draw tail indent
            pos = txtTailIndent
            # tail indent could be negative
            if pos <= 0:
                # substract from width of the text box
                pos = w + pos
            stroke(0, 0, 1)
            line((x+pos, y), (x+pos, y+h))
            # draw a rectangle
            fill(0, .1)
            stroke(None)
            rect(x, y, w, h)

            # create a formatted string
            t = FormattedString()
            # set alignment
            t.align("justified")
            # add text
            t += txt
            # add hard return
            t += "\\n"
            # set style for indented text
            t.fontSize(6)
            t.paragraphTopSpacing(paragraphTop)
            t.paragraphBottomSpacing(paragraphBottom)
            t.firstLineIndent(txtFirstLineIndent)
            t.indent(txtIndent)
            t.tailIndent(txtTailIndent)
            # add text
            t += txt
            # add hard return
            t += "\\n"
            # reset style
            t.fontSize(10)
            t.indent(None)
            t.tailIndent(None)
            t.firstLineIndent(None)
            t.paragraphTopSpacing(None)
            t.paragraphBottomSpacing(None)
            # add text
            t += txt
            # draw formatted string in a text box
            textBox(t, (x, y, w, h))
        """
        self._indent = indent

    def tailIndent(self, indent):
        """
        Set indent of text right of the paragraph.
        """
        self._tailIndent = indent

    def firstLineIndent(self, indent):
        """
        Set indent of the text only for the first line.
        """
        self._firstLineIndent = indent

    def paragraphTopSpacing(self, value):
        """
        set paragraph spacing at the top.
        """
        self._paragraphTopSpacing = value

    def paragraphBottomSpacing(self, value):
        """
        set paragraph spacing at the bottom.
        """
        self._paragraphBottomSpacing = value

    def language(self, language):
        """
        Set the preferred language as language tag or None to use the default language.
        """
        self._language = language

    def size(self):
        """
        Return the size of the text.
        """
        return self._attributedString.size()

    def getNSObject(self):
        return self._attributedString

    def copy(self):
        """
        Copy the formatted string.
        """
        attributes = {key: getattr(self, "_%s" % key) for key in self._formattedAttributes}
        new = self.__class__(**attributes)
        new._attributedString = self._attributedString.mutableCopy()
        return new

    def fontAscender(self):
        """
        Returns the current font ascender, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.ascender()

    def fontDescender(self):
        """
        Returns the current font descender, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.descender()

    def fontXHeight(self):
        """
        Returns the current font x-height, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.xHeight()

    def fontCapHeight(self):
        """
        Returns the current font cap height, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.capHeight()

    def fontLeading(self):
        """
        Returns the current font leading, based on the current `font` and `fontSize`.
        """
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.leading()

    def fontLineHeight(self):
        """
        Returns the current line height, based on the current `font` and `fontSize`.
        If a `lineHeight` is set, this value will be returned.
        """
        if self._lineHeight is not None:
            return self._lineHeight
        font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            ff = self._fallbackFont or _FALLBACKFONT
            warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, ff))
            font = AppKit.NSFont.fontWithName_size_(ff, self._fontSize)
        return font.defaultLineHeightForFont()

    def appendGlyph(self, *glyphNames):
        """
        Append a glyph by his glyph name using the current `font`.
        Multiple glyph names are possible.

        .. downloadcode:: appendGlyphFormattedString.py

            # create an empty formatted string object
            t = FormattedString()
            # set a font
            t.font("Menlo-Regular")
            # set a font size
            t.fontSize(60)
            # add some glyphs
            t.appendGlyph("Eng", "Eng.alt")
            # draw the formatted string
            text(t, (10, 100))
        """
        # use a non breaking space as replacement character
        baseString = unichr(0x00A0)
        font = None
        if self._font:
            font = AppKit.NSFont.fontWithName_size_(self._font, self._fontSize)
        if font is None:
            warnings.warn("font: '%s' is not installed, back to the fallback font: '%s'" % (self._font, _FALLBACKFONT))
            font = AppKit.NSFont.fontWithName_size_(_FALLBACKFONT, self._fontSize)

        # disable calt features, as this seems to be on by default
        # for both the font stored in the nsGlyphInfo as in the replacement character
        fontAttributes = {}
        fontAttributes[CoreText.NSFontFeatureSettingsAttribute] = [openType.featureMap["calt_off"]]
        fontDescriptor = font.fontDescriptor()
        fontDescriptor = fontDescriptor.fontDescriptorByAddingAttributes_(fontAttributes)
        font = AppKit.NSFont.fontWithDescriptor_size_(fontDescriptor, self._fontSize)

        fallbackFont = self._fallbackFont
        self._fallbackFont = None
        _openTypeFeatures = dict(self._openTypeFeatures)
        self._openTypeFeatures = dict(calt=False)
        for glyphName in glyphNames:
            glyph = font.glyphWithName_(glyphName)
            if glyph:
                self.append(baseString)
                glyphInfo = AppKit.NSGlyphInfo.glyphInfoWithGlyph_forFont_baseString_(glyph, font, baseString)
                self._attributedString.addAttribute_value_range_(AppKit.NSGlyphInfoAttributeName, glyphInfo, (len(self) - 1, 1))
            else:
                warnings.warn("font '%s' has no glyph with the name '%s'" % (font.fontName(), glyphName))
        self.openTypeFeatures(**_openTypeFeatures)
        self._fallbackFont = fallbackFont


class GraphicsState(object):

    _textClass = FormattedString
    _colorClass = Color

    def __init__(self):
        self.colorSpace = self._colorClass.colorSpace
        self.blendMode = None
        self.fillColor = self._colorClass(0)
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
        self.hyphenation = None
        self.path = None

    def copy(self):
        new = self.__class__()
        new.colorSpace = self.colorSpace
        new.blendMode = self.blendMode
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
        new.hyphenation = self.hyphenation
        new.strokeWidth = self.strokeWidth
        new.lineCap = self.lineCap
        if self.lineDash is not None:
            new.lineDash = list(self.lineDash)
        new.lineJoin = self.lineJoin
        new.miterLimit = self.miterLimit
        return new

    def update(self, context):
        self.updateColorSpace(context)

    # support for color spaces

    def setColorSpace(self, colorSpace):
        self.colorSpace = colorSpace
        self.updateColorSpace(None)

    def updateColorSpace(self, context):
        self._colorClass.colorSpace = self.colorSpace


class BaseContext(object):

    _graphicsStateClass = GraphicsState

    _cmykColorClass = CMYKColor
    _colorClass = Color
    _textClass = FormattedString
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

    _textAlignMap = FormattedString._textAlignMap
    _textTabAlignMap = FormattedString._textTabAlignMap
    _textUnderlineMap = FormattedString._textUnderlineMap

    _colorSpaceMap = dict(
        genericRGB=AppKit.NSColorSpace.genericRGBColorSpace,
        adobeRGB1998=AppKit.NSColorSpace.adobeRGB1998ColorSpace,
        sRGB=AppKit.NSColorSpace.sRGBColorSpace,
        genericGray=AppKit.NSColorSpace.genericGrayColorSpace,
        genericGamma22Gray=AppKit.NSColorSpace.genericGamma22GrayColorSpace,
    )

    _blendModeMap = dict(
        normal=Quartz.kCGBlendModeNormal,
        multiply=Quartz.kCGBlendModeMultiply,
        screen=Quartz.kCGBlendModeScreen,
        overlay=Quartz.kCGBlendModeOverlay,
        darken=Quartz.kCGBlendModeDarken,
        lighten=Quartz.kCGBlendModeLighten,
        colorDodge=Quartz.kCGBlendModeColorDodge,
        colorBurn=Quartz.kCGBlendModeColorBurn,
        softLight=Quartz.kCGBlendModeSoftLight,
        hardLight=Quartz.kCGBlendModeHardLight,
        difference=Quartz.kCGBlendModeDifference,
        exclusion=Quartz.kCGBlendModeExclusion,
        hue=Quartz.kCGBlendModeHue,
        saturation=Quartz.kCGBlendModeSaturation,
        color=Quartz.kCGBlendModeColor,
        luminosity=Quartz.kCGBlendModeLuminosity,
        clear=Quartz.kCGBlendModeClear,
        copy=Quartz.kCGBlendModeCopy,
        sourceIn=Quartz.kCGBlendModeSourceIn,
        sourceOut=Quartz.kCGBlendModeSourceOut,
        sourceAtop=Quartz.kCGBlendModeSourceAtop,
        destinationOver=Quartz.kCGBlendModeDestinationOver,
        destinationIn=Quartz.kCGBlendModeDestinationIn,
        destinationOut=Quartz.kCGBlendModeDestinationOut,
        destinationAtop=Quartz.kCGBlendModeDestinationAtop,
        xOR=Quartz.kCGBlendModeXOR,
        plusDarker=Quartz.kCGBlendModePlusDarker,
        plusLighter=Quartz.kCGBlendModePlusLighter,
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

    def _blendMode(self, operation):
        pass

    def _drawPath(self):
        pass

    def _clipPath(self):
        pass

    def _transform(self, matrix):
        pass

    def _textBox(self, txt, box, align):
        pass

    def _image(self, path, (x, y), alpha, pageNumber):
        pass

    def _frameDuration(self, seconds):
        pass

    def _reset(self, other=None):
        pass

    def _saveImage(self, path, multipage):
        pass

    def _printImage(self, pdf=None):
        pass

    def _linkDestination(self, name, (x, y)):
        pass

    def _linkRect(self, name, (x, y, w, h)):
        pass

    #

    def reset(self):
        self._stack = []
        self._state = self._graphicsStateClass()
        self._colorClass.colorSpace = self._colorSpaceMap['genericRGB']
        self._reset()

    def size(self, width=None, height=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

    def newPage(self, width=None, height=None):
        if self.width is None and width is None:
            raise DrawBotError("A page must have a width")
        if self.height is None and height is None:
            raise DrawBotError("A page must have a height")
        self.hasPage = True
        self._newPage(width, height)

    def saveImage(self, path, multipage):
        if not self.hasPage:
            raise DrawBotError("can't save image when no page is set")
        self._saveImage(path, multipage)

    def printImage(self, pdf=None):
        self._printImage(pdf)

    def frameDuration(self, seconds):
        self._frameDuration(seconds)

    def save(self):
        self._stack.append(self._state.copy())
        self._save()

    def restore(self):
        if not self._stack:
            raise DrawBotError("can't restore graphics state: no matching save()")
        self._state = self._stack.pop()
        self._state.update(self)
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
            raise DrawBotError("Create a new path first")
        self._state.path.moveTo(pt)

    def lineTo(self, pt):
        self._state.path.lineTo(pt)

    def curveTo(self, pt1, pt2, pt):
        self._state.path.curveTo(pt1, pt2, pt)

    def arc(self, center, radius, startAngle, endAngle, clockwise):
        self._state.path.arc(center, radius, startAngle, endAngle, clockwise)

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

    def colorSpace(self, colorSpace):
        if colorSpace is None:
            colorSpace = 'genericRGB'
        if colorSpace not in self._colorSpaceMap:
            raise DrawBotError("'%s' is not a valid colorSpace, argument must be '%s'" % (colorSpace, "', '".join(self._colorSpaceMap.keys())))
        colorSpace = self._colorSpaceMap[colorSpace]
        self._state.setColorSpace(colorSpace)

    def blendMode(self, operation):
        self._state.blendMode = operation
        self._blendMode(operation)

    def fill(self, r, g=None, b=None, a=1):
        self._state.text.fill(r, g, b, a)
        self._state.cmykFillColor = None
        if r is None:
            self._state.fillColor = None
            return
        self._state.fillColor = self._colorClass(r, g, b, a)
        self._state.gradient = None

    def cmykFill(self, c, m, y, k, a=1):
        self._state.text.cmykFill(c, m, y, k, a)
        if c is None:
            self.fill(None)
        else:
            self._state.cmykFillColor = self._cmykColorClass(c, m, y, k, a)
            r, g, b = cmyk2rgb(c, m, y, k)
            self._state.fillColor = self._colorClass(r, g, b, a)
            self._state.gradient = None

    def stroke(self, r, g=None, b=None, a=1):
        self._state.text.stroke(r, g, b, a)
        self._state.cmykStrokeColor = None
        if r is None:
            self._state.strokeColor = None
            return
        self._state.strokeColor = self._colorClass(r, g, b, a)

    def cmykStroke(self, c, m, y, k, a=1):
        self._state.text.cmykStroke(c, m, y, k, a)
        if c is None:
            self.stroke(None)
        else:
            self._state.cmykStrokeColor = self._cmykColorClass(c, m, y, k, a)
            r, g, b = cmyk2rgb(c, m, y, k)
            self._state.strokeColor = self._colorClass(r, g, b, a)

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
            self.fill(0)
            return
        self._state.gradient = self._gradientClass("linear", startPoint, endPoint, colors, locations)
        self.fill(None)

    def cmykLinearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        if startPoint is None:
            self._state.gradient = None
            self.fill(0)
            return
        rgbColors = [cmyk2rgb(color[0], color[1], color[2], color[3]) for color in colors]
        self._state.gradient = self._gradientClass("linear", startPoint, endPoint, rgbColors, locations)
        self._state.gradient.cmykColors = [self._cmykColorClass(*color) for color in colors]
        self.fill(None)

    def radialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        if startPoint is None:
            self._state.gradient = None
            self.fill(0)
            return
        self._state.gradient = self._gradientClass("radial", startPoint, endPoint, colors, locations, startRadius, endRadius)
        self.fill(None)

    def cmykRadialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        if startPoint is None:
            self._state.gradient = None
            self.fill(0)
            return
        rgbColors = [cmyk2rgb(color[0], color[1], color[2], color[3]) for color in colors]
        self._state.gradient = self._gradientClass("radial", startPoint, endPoint, rgbColors, locations, startRadius, endRadius)
        self._state.gradient.cmykColors = [self._cmykColorClass(*color) for color in colors]
        self.fill(None)

    def strokeWidth(self, value):
        self._state.text.strokeWidth(value)
        self._state.strokeWidth = value

    def miterLimit(self, value):
        self._state.miterLimit = value

    def lineJoin(self, join):
        if join is None:
            self._state.lineJoin = None
        if join not in self._lineJoinStylesMap:
            raise DrawBotError("lineJoin() argument must be 'bevel', 'miter' or 'round'")
        self._state.lineJoin = self._lineJoinStylesMap[join]

    def lineCap(self, cap):
        if cap is None:
            self._state.lineCap = None
        if cap not in self._lineCapStylesMap:
            raise DrawBotError("lineCap() argument must be 'butt', 'square' or 'round'")
        self._state.lineCap = self._lineCapStylesMap[cap]

    def lineDash(self, dash):
        if dash[0] is None:
            self._state.lineDash = None
            return
        self._state.lineDash = list(dash)

    def transform(self, matrix):
        self._transform(matrix)

    def font(self, fontName, fontSize):
        return self._state.text.font(fontName, fontSize)

    def fallbackFont(self, fontName):
        self._state.text.fallbackFont(fontName)

    def fontSize(self, fontSize):
        self._state.text.fontSize(fontSize)

    def lineHeight(self, lineHeight):
        self._state.text.lineHeight(lineHeight)

    def tracking(self, tracking):
        self._state.text.tracking(tracking)

    def baselineShift(self, baselineShift):
        self._state.text.baselineShift(baselineShift)

    def underline(self, underline):
        self._state.text.underline(underline)

    def hyphenation(self, value):
        self._state.hyphenation = value

    def tabs(self, *tabs):
        self._state.text.tabs(*tabs)

    def language(self, language):
        self._state.text.language(language)

    def openTypeFeatures(self, *args, **features):
        self._state.text.openTypeFeatures(*args, **features)

    def fontVariations(self, *args, **axes):
        self._state.text.fontVariations(*args, **axes)

    def attributedString(self, txt, align=None):
        if isinstance(txt, FormattedString):
            return txt.getNSObject()
        self._state.text.clear()
        self._state.text.append(txt, align=align)
        return self._state.text.getNSObject()

    def hyphenateAttributedString(self, attrString, path):
        # add soft hyphens
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

        # get the lines
        lines = self._getTypesetterLinesWithPath(attrString, path)
        # get all lines justified
        justifiedLines = self._getTypesetterLinesWithPath(self._justifyAttributedString(attrString), path)

        # loop over all lines
        i = 0
        while i < len(lines):
            # get the current line
            line = lines[i]
            # get the range in the text for the current line
            rng = CoreText.CTLineGetStringRange(line)
            # get the substring from the range
            subString = attrString.attributedSubstringFromRange_(rng)
            # get the string
            subStringText = subString.string()
            # check if the line ends with a softhypen
            if len(subStringText) and subStringText[-1] == unichr(self._softHypen):
                # here we go
                # get the justified line and get the max line width
                maxLineWidth, a, d, l = CoreText.CTLineGetTypographicBounds(justifiedLines[i], None, None, None)
                # get the last attributes
                hyphenAttr, _ = subString.attributesAtIndex_effectiveRange_(0, None)
                # create a hyphen string
                hyphenAttrString = AppKit.NSAttributedString.alloc().initWithString_attributes_("-", hyphenAttr)
                # get the width of the hyphen
                hyphenWidth = hyphenAttrString.size().width
                # get all line break location of that line
                lineBreakLocation = len(subString)
                possibleLineBreaks = [lineBreakLocation]
                while lineBreakLocation:
                    lineBreakLocation = subString.lineBreakBeforeIndex_withinRange_(lineBreakLocation, (0, len(subString)))
                    if lineBreakLocation:
                        possibleLineBreaks.append(lineBreakLocation)
                breakFound = False
                # loop over all possible line breaks
                while possibleLineBreaks:
                    lineBreak = possibleLineBreaks.pop(0)
                    # get a possible line
                    breakString = subString.attributedSubstringFromRange_((0, lineBreak))
                    # get the width
                    stringWidth = breakString.size().width
                    # add hyphen width if required
                    if breakString.string()[-1] == unichr(self._softHypen):
                        stringWidth += hyphenWidth
                    # found a break
                    if stringWidth <= maxLineWidth:
                        breakFound = True
                        break

                if breakFound and len(breakString.string()) > 2 and breakString.string()[-1] == unichr(self._softHypen):
                    # if the break line ends with a soft hyphen
                    # add a hyphen
                    attrString.replaceCharactersInRange_withString_((rng.location + lineBreak, 0), "-")
                # remove all soft hyphens for the range of that line
                mutString.replaceOccurrencesOfString_withString_options_range_(unichr(self._softHypen), "", AppKit.NSLiteralSearch, rng)
                # reset the lines, from the adjusted attribute string
                lines = self._getTypesetterLinesWithPath(attrString, path)
                # reset the justifed lines form the adjusted attributed string
                justifiedLines = self._getTypesetterLinesWithPath(self._justifyAttributedString(attrString), path)
            # next line
            i += 1
        # remove all soft hyphen
        mutString.replaceOccurrencesOfString_withString_options_range_(unichr(self._softHypen), "", AppKit.NSLiteralSearch, (0, mutString.length()))
        # done!
        return attrString

    def clippedText(self, txt, box, align):
        path, origin = self._getPathForFrameSetter(box)
        attrString = self.attributedString(txt, align=align)
        if self._state.hyphenation:
            hyphenIndexes = [i for i, c in enumerate(attrString.string()) if c == "-"]
            attrString = self.hyphenateAttributedString(attrString, path)
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        visibleRange = CoreText.CTFrameGetVisibleStringRange(box)
        clip = visibleRange.length
        if self._state.hyphenation:
            subString = attrString.string()[:clip]
            for i in hyphenIndexes:
                if i < clip:
                    clip += 1
                else:
                    break
            clip -= subString.count("-")
        return txt[clip:]

    def _justifyAttributedString(self, attr):
        # create a justified copy of the attributed string
        attr = attr.mutableCopy()

        def changeParaAttribute(para, rng, _):
            para = para.mutableCopy()
            para.setAlignment_(AppKit.NSJustifiedTextAlignment)
            attr.addAttribute_value_range_(AppKit.NSParagraphStyleAttributeName, para, rng)

        attr.enumerateAttribute_inRange_options_usingBlock_(AppKit.NSParagraphStyleAttributeName, (0, len(attr)), 0, changeParaAttribute)
        return attr

    def _getTypesetterLinesWithPath(self, attrString, path, offset=None):
        # get lines for an attribute string with a given path
        if offset is None:
            offset = 0, 0
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        frame = CoreText.CTFramesetterCreateFrame(setter, offset, path, None)
        return CoreText.CTFrameGetLines(frame)

    def _getPathForFrameSetter(self, box):
        if isinstance(box, self._bezierPathClass):
            path = box._getCGPath()
            (x, y), (w, h) = CoreText.CGPathGetPathBoundingBox(path)
        else:
            x, y, w, h = box
            path = CoreText.CGPathCreateMutable()
            CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(x, y, w, h))
        return path, (x, y)

    def textSize(self, txt, align, width, height):
        attrString = self.attributedString(txt, align)
        if width is None:
            w, h = attrString.size()
        else:
            if width is None:
                width = CoreText.CGFLOAT_MAX
            if height is None:
                height = CoreText.CGFLOAT_MAX
            if self._state.hyphenation:
                path = CoreText.CGPathCreateMutable()
                CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(0, 0, width, height))
                attrString = self.hyphenateAttributedString(attrString, path)
            setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
            (w, h), _ = CoreText.CTFramesetterSuggestFrameSizeWithConstraints(setter, (0, 0), None, (width, height), None)
        return w, h

    def textBox(self, txt, box, align="left"):
        self._state.path = None
        self._textBox(txt, box, align)

    def image(self, path, (x, y), alpha, pageNumber):
        self._image(path, (x, y), alpha, pageNumber)

    def installFont(self, path):
        url = AppKit.NSURL.fileURLWithPath_(path)
        success, error = CoreText.CTFontManagerRegisterFontsForURL(url, CoreText.kCTFontManagerScopeProcess, None)
        if not success:
            error = error.localizedDescription()
        return success, error

    def uninstallFont(self, path):
        url = AppKit.NSURL.fileURLWithPath_(path)
        success, error = CoreText.CTFontManagerUnregisterFontsForURL(url, CoreText.kCTFontManagerScopeProcess, None)
        if not success:
            error = error.localizedDescription()
        return success, error

    def _fontNameForPath(self, path):
        from fontTools.ttLib import TTFont, TTLibError
        try:
            font = TTFont(path, fontNumber=0)  # in case of .ttc, use the first font
            psName = font["name"].getName(6, 1, 0)
            if psName is None:
                psName = font["name"].getName(6, 3, 1)
            font.close()
        except IOError:
            raise DrawBotError("Font '%s' does not exist." % path)
        except TTLibError:
            raise DrawBotError("Font '%s' is not a valid font." % path)
        if psName is not None:
            psName = psName.toUnicode()
        return psName

    def linkDestination(self, name, (x, y)):
        self._linkDestination(name, (x, y))

    def linkRect(self, name, (x, y, w, h)):
        self._linkRect(name, (x, y, w, h))
