import AppKit
import CoreText
import Quartz

import math
import os

from fontTools.pens.basePen import BasePen

from drawBot.misc import DrawBotError, cmyk2rgb, warnings, transformationAtCenter
from drawBot.macOSVersion import macOSVersion
from drawBot.misc import memoize

from .tools import openType
from .tools import variation
from .tools import SFNTLayoutTypes


_FALLBACKFONT = "LucidaGrande"
_LINEJOINSTYLESMAP = dict(
    miter=Quartz.kCGLineJoinMiter,
    round=Quartz.kCGLineJoinRound,
    bevel=Quartz.kCGLineJoinBevel
)
_LINECAPSTYLESMAP = dict(
    butt=Quartz.kCGLineCapButt,
    square=Quartz.kCGLineCapSquare,
    round=Quartz.kCGLineCapRound,
)


# context specific attributes

class ContextPropertyMixin:

    def copyContextProperties(self, other):
        # loop over all base classes
        for cls in self.__class__.__bases__:
            func = getattr(cls, "_copyContextProperties", None)
            if func is not None:
                func(self, other)


class contextProperty:

    def __init__(self, doc, validator=None):
        self.__doc__ = doc
        if validator is not None:
            validator = getattr(self, f"_{validator}")
        self._validator = validator

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        if self._validator:
            self._validator(value)
        obj.__dict__[self.name] = value

    def __delete__(self, obj):
        obj.__dict__.pop(self.name, None)

    def _stringValidator(self, value):
        if value is None:
            return
        if not isinstance(value, str):
            raise DrawBotError(f"'{self.name}' must be a string.")


class SVGContextPropertyMixin:

    svgID = contextProperty("The svg id, as a string.", "stringValidator")
    svgClass = contextProperty("The svg class, as a string.", "stringValidator")
    svgLink = contextProperty("The svg link, as a string.", "stringValidator")

    def _copyContextProperties(self, other):
        self.svgID = other.svgID
        self.svgClass = other.svgClass
        self.svgLink = other.svgLink


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
        return tuple([point for segment in self for point in segment])

    points = property(_get_points, doc="Return an immutable list of all the points in the contour as point coordinate `(x, y)` tuples.")


class BezierPath(BasePen, SVGContextPropertyMixin, ContextPropertyMixin):

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
            self._path = AppKit.NSBezierPath.alloc().init()
        else:
            self._path = path
        BasePen.__init__(self, glyphSet)

    def __repr__(self):
        return "<BezierPath>"

    # pen support

    def moveTo(self, point):
        """
        Move to a point `x`, `y`.
        """
        super(BezierPath, self).moveTo(point)

    def _moveTo(self, pt):
        self._path.moveToPoint_(pt)

    def lineTo(self, point):
        """
        Line to a point `x`, `y`.
        """
        super(BezierPath, self).lineTo(point)

    def _lineTo(self, pt):
        self._path.lineToPoint_(pt)

    def curveTo(self, *points):
        """
        Draw a cubic bezier with an arbitrary number of control points.

        The last point specified is on-curve, all others are off-curve
        (control) points.
        """
        super(BezierPath, self).curveTo(*points)

    def qCurveTo(self, *points):
        """
        Draw a whole string of quadratic curve segments.

        The last point specified is on-curve, all others are off-curve
        (control) points.
        """
        super(BezierPath, self).qCurveTo(*points)

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
        Begin using the path as a so called point pen and start a new subpath.
        """
        from fontTools.pens.pointPen import PointToSegmentPen
        self._pointToSegmentPen = PointToSegmentPen(self)
        self._pointToSegmentPen.beginPath()

    def addPoint(self, point, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        """
        Use the path as a point pen and add a point to the current subpath. `beginPath` must
        have been called prior to adding points with `addPoint` calls.
        """
        if not hasattr(self, "_pointToSegmentPen"):
            raise DrawBotError("path.beginPath() must be called before the path can be used as a point pen")
        self._pointToSegmentPen.addPoint(
            point,
            segmentType=segmentType,
            smooth=smooth,
            name=name,
            identifier=identifier,
            **kwargs
        )

    def endPath(self):
        """
        End the current subpath. Calling this method has two distinct meanings depending
        on the context:

        When the bezier path is used as a segment pen (using `moveTo`, `lineTo`, etc.),
        the current subpath will be finished as an open contour.

        When the bezier path is used as a point pen (using `beginPath`, `addPoint` and
        `endPath`), the path will process all the points added with `addPoint`, finishing
        the current subpath.
        """
        if hasattr(self, "_pointToSegmentPen"):
            # its been used in a point pen world
            pointToSegmentPen = self._pointToSegmentPen
            del self._pointToSegmentPen
            pointToSegmentPen.endPath()
        else:
            # with NSBezierPath, nothing special needs to be done for an open subpath.
            pass

    def addComponent(self, glyphName, transformation):
        """
        Add a sub glyph. The 'transformation' argument must be a 6-tuple
        containing an affine transformation, or a Transform object from the
        fontTools.misc.transform module. More precisely: it should be a
        sequence containing 6 numbers.

        A `glyphSet` is required during initialization of the BezierPath object.
        """
        super(BezierPath, self).addComponent(glyphName, transformation)

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

    def arcTo(self, point1, point2, radius):
        """
        Arc  defined by a circle inscribed inside the angle specified by three points:
        the current point, `point1`, and `point2`. The arc is drawn between the two points of the circle that are tangent to the two legs of the angle.
        """
        self._path.appendBezierPathWithArcFromPoint_toPoint_radius_(point1, point2, radius)

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

    def line(self, point1, point2):
        """
        Add a line between two given points.
        """
        self.moveTo(point1)
        self.lineTo(point2)

    def polygon(self, *points, **kwargs):
        """
        Draws a polygon with n-amount of points.
        Optionally a `close` argument can be provided to open or close the path.
        As default a `polygon` is a closed path.
        """
        if len(points) <= 1:
            raise TypeError("polygon() expects more than a single point")
        doClose = kwargs.get("close", True)
        if (len(kwargs) == 1 and "close" not in kwargs) or len(kwargs) > 1:
            raise TypeError("unexpected keyword argument for this function")

        self.moveTo(points[0])
        for x, y in points[1:]:
            self.lineTo((x, y))
        if doClose:
            self.closePath()

    def text(self, txt, offset=None, font=_FALLBACKFONT, fontSize=10, align=None, fontNumber=0):
        """
        Draws a `txt` with a `font` and `fontSize` at an `offset` in the bezier path.
        If a font path is given the font will be installed and used directly.

        Optionally an alignment can be set.
        Possible `align` values are: `"left"`, `"center"` and `"right"`.

        The default alignment is `left`.

        Optionally `txt` can be a `FormattedString`.
        """
        if not isinstance(txt, (str, FormattedString)):
            raise TypeError("expected 'str' or 'FormattedString', got '%s'" % type(txt).__name__)
        if align and align not in BaseContext._textAlignMap.keys():
            raise DrawBotError("align must be %s" % (", ".join(BaseContext._textAlignMap.keys())))

        context = BaseContext()
        context.font(font, fontSize, fontNumber)
        attributedString = context.attributedString(txt, align)
        if offset:
            x, y = offset
        else:
            x = y = 0
        for subTxt, box in makeTextBoxes(attributedString, (x, y), align=align, plainText=not isinstance(txt, FormattedString)):
            self.textBox(subTxt, box, font=font, fontSize=fontSize, align=align)

    def textBox(self, txt, box, font=_FALLBACKFONT, fontSize=10, align=None, hyphenation=None, fontNumber=0):
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
        if not isinstance(txt, (str, FormattedString)):
            raise TypeError("expected 'str' or 'FormattedString', got '%s'" % type(txt).__name__)
        if align and align not in BaseContext._textAlignMap.keys():
            raise DrawBotError("align must be %s" % (", ".join(BaseContext._textAlignMap.keys())))
        context = BaseContext()
        context.font(font, fontSize, fontNumber)
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
        from .tools import traceImage
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
        return path

    def _setCGPath(self, cgpath):
        self._path = AppKit.NSBezierPath.alloc().init()

        def _addPoints(arg, element):
            instruction, points = element.type, element.points
            if instruction == Quartz.kCGPathElementMoveToPoint:
                self._path.moveToPoint_(points[0])
            elif instruction == Quartz.kCGPathElementAddLineToPoint:
                self._path.lineToPoint_(points[0])
            elif instruction == Quartz.kCGPathElementAddCurveToPoint:
                self._path.curveToPoint_controlPoint1_controlPoint2_(points[2], points[0], points[1])
            elif instruction == Quartz.kCGPathElementCloseSubpath:
                self._path.closePath()
        Quartz.CGPathApply(cgpath, None, _addPoints)

    def setNSBezierPath(self, path):
        """
        Set a nsBezierPath.
        """
        self._path = path

    def pointInside(self, xy):
        """
        Check if a point `x`, `y` is inside a path.
        """
        x, y = xy
        return self._path.containsPoint_((x, y))

    def bounds(self):
        """
        Return the bounding box of the path in the form
        `(x minimum, y minimum, x maximum, y maximum)`` or,
        in the case of empty path `None`.
        """
        if self._path.isEmpty():
            return None
        (x, y), (w, h) = self._path.bounds()
        return x, y, x + w, y + h

    def controlPointBounds(self):
        """
        Return the bounding box of the path including the offcurve points
        in the form `(x minimum, y minimum, x maximum, y maximum)`` or,
        in the case of empty path `None`.
        """
        (x, y), (w, h) = self._path.controlPointBounds()
        return x, y, x + w, y + h

    def optimizePath(self):
        count = self._path.elementCount()
        if not count or self._path.elementAtIndex_(count - 1) != AppKit.NSMoveToBezierPathElement:
            return
        optimizedPath = AppKit.NSBezierPath.alloc().init()
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
        new.copyContextProperties(self)
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

    def rotate(self, angle, center=(0, 0)):
        """
        Rotate the path around the `center` point (which is the origin by default) with a given angle in degrees.
        """
        angle = math.radians(angle)
        c = math.cos(angle)
        s = math.sin(angle)
        self.transform((c, s, -s, c, 0, 0), center)

    def scale(self, x=1, y=None, center=(0, 0)):
        """
        Scale the path with a given `x` (horizontal scale) and `y` (vertical scale).

        If only 1 argument is provided a proportional scale is applied.

        The center of scaling can optionally be set via the `center` keyword argument. By default this is the origin.
        """
        if y is None:
            y = x
        self.transform((x, 0, 0, y, 0, 0), center)

    def skew(self, angle1, angle2=0, center=(0, 0)):
        """
        Skew the path with given `angle1` and `angle2`.

        If only one argument is provided a proportional skew is applied.

        The center of skewing can optionally be set via the `center` keyword argument. By default this is the origin.
        """
        angle1 = math.radians(angle1)
        angle2 = math.radians(angle2)
        self.transform((1, math.tan(angle2), math.tan(angle1), 1, 0, 0), center)

    def transform(self, transformMatrix, center=(0, 0)):
        """
        Transform a path with a transform matrix (xy, xx, yy, yx, x, y).
        """
        if center != (0, 0):
            transformMatrix = transformationAtCenter(transformMatrix, center)
        aT = AppKit.NSAffineTransform.alloc().init()
        aT.setTransformStruct_(transformMatrix[:])
        self._path.transformUsingAffineTransform_(aT)

    # boolean operations

    def _contoursForBooleanOperations(self):
        # contours are very temporaly objects
        # redirect drawToPointPen to drawPoints
        contours = self.contours
        for contour in contours:
            contour.drawPoints = contour.drawToPointPen
            if contour.open:
                raise DrawBotError("open contours are not supported during boolean operations")
        return contours

    def union(self, other):
        """
        Return the union between two bezier paths.
        """
        assert isinstance(other, self.__class__)
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
        assert isinstance(other, self.__class__)
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
        assert isinstance(other, self.__class__)
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
        assert isinstance(other, self.__class__)
        import booleanOperations
        subjectContours = self._contoursForBooleanOperations()
        clipContours = other._contoursForBooleanOperations()
        result = self.__class__()
        booleanOperations.xor(subjectContours, clipContours, result)
        return result

    def intersectionPoints(self, other=None):
        """
        Return a list of intersection points as `x`, `y` tuples.

        Optionaly provide an other path object to find intersection points.
        """
        import booleanOperations
        contours = self._contoursForBooleanOperations()
        if other is not None:
            assert isinstance(other, self.__class__)
            contours += other._contoursForBooleanOperations()
        return booleanOperations.getIntersections(contours)

    def expandStroke(self, width, lineCap="round", lineJoin="round", miterLimit=10):
        """
        Returns a new bezier path with an expanded stroke around the original path,
        with a given `width`. Note: the new path will not contain the original path.

        The following optional arguments are available with respect to line caps and joins:
        * `lineCap`: Possible values are `"butt"`, `"square"` or `"round"`
        * `lineJoin`: Possible values are `"bevel"`, `"miter"` or `"round"`
        * `miterLimit`: The miter limit to use for `"miter"` lineJoin option
        """
        if lineJoin not in _LINEJOINSTYLESMAP:
            raise DrawBotError("lineJoin must be 'bevel', 'miter' or 'round'")
        if lineCap not in _LINECAPSTYLESMAP:
            raise DrawBotError("lineCap must be 'butt', 'square' or 'round'")

        strokedCGPath = Quartz.CGPathCreateCopyByStrokingPath(self._getCGPath(), None, width, _LINECAPSTYLESMAP[lineCap], _LINEJOINSTYLESMAP[lineJoin], miterLimit)
        result = self.__class__()
        result._setCGPath(strokedCGPath)
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
        return tuple(points)

    def _get_points(self):
        return self._points()

    points = property(_get_points, doc="Return an immutable list of all points in the BezierPath as point coordinate `(x, y)` tuples.")

    def _get_onCurvePoints(self):
        return self._points(offCurve=False)

    onCurvePoints = property(_get_onCurvePoints, doc="Return an immutable list of all on curve points in the BezierPath as point coordinate `(x, y)` tuples.")

    def _get_offCurvePoints(self):
        return self._points(onCurve=False)

    offCurvePoints = property(_get_offCurvePoints, doc="Return an immutable list of all off curve points in the BezierPath as point coordinate `(x, y)` tuples.")

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
        return tuple(contours)

    contours = property(_get_contours, doc="Return an immutable list of contours with all point coordinates sorted in segments. A contour object has an `open` attribute.")

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

    colorSpace = AppKit.NSColorSpace.genericRGBColorSpace()

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
        self._color = self._color.colorUsingColorSpace_(self.colorSpace)

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
    def getColorsFromList(cls, inputColors):
        outputColors = []
        for color in inputColors:
            color = cls.getColor(color)
            outputColors.append(color)
        return outputColors

    @classmethod
    def getColor(cls, color):
        if isinstance(color, cls.__class__):
            return color
        elif isinstance(color, (tuple, list)):
            return cls(*color)
        elif isinstance(color, AppKit.NSColor):
            return cls(color)
        raise DrawBotError("Not a valid color: %s" % color)


class CMYKColor(Color):

    colorSpace = AppKit.NSColorSpace.genericCMYKColorSpace()

    def __init__(self, c=None, m=None, y=None, k=None, a=1):
        if c is None:
            return
        if isinstance(c, AppKit.NSColor):
            self._color = c
        else:
            self._color = AppKit.NSColor.colorWithDeviceCyan_magenta_yellow_black_alpha_(c, m, y, k, a)
        self._color = self._color.colorUsingColorSpace_(self.colorSpace)
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


def makeTextBoxes(attributedString, xy, align, plainText):
    extraPadding = 20
    x, y = xy
    w, h = attributedString.size()
    w += extraPadding

    if align is not None:
        attributedString = attributedString.mutableCopy()
        # overwrite all align settings in each paragraph style
        def block(value, rng, stop):
            value = value.mutableCopy()
            value.setAlignment_(FormattedString._textAlignMap[align])
            attributedString.addAttribute_value_range_(AppKit.NSParagraphStyleAttributeName, value, rng)
        attributedString.enumerateAttribute_inRange_options_usingBlock_(AppKit.NSParagraphStyleAttributeName, (0, len(attributedString)), 0, block)

    setter = CoreText.CTFramesetterCreateWithAttributedString(attributedString)
    path = Quartz.CGPathCreateMutable()
    Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w, h * 2))
    frame = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
    ctLines = CoreText.CTFrameGetLines(frame)
    origins = CoreText.CTFrameGetLineOrigins(frame, (0, len(ctLines)), None)
    boxes = []
    if not origins:
        return boxes

    firstLineJump = h * 2 - origins[0].y

    isFirstLine = True
    for ctLine, (originX, originY) in zip(ctLines, origins):
        rng = CoreText.CTLineGetStringRange(ctLine)

        attributedSubstring = attributedString.attributedSubstringFromRange_(rng)
        para, _ = attributedSubstring.attribute_atIndex_effectiveRange_(AppKit.NSParagraphStyleAttributeName, 0, None)

        width, height = attributedSubstring.size()

        if attributedSubstring.length() > 0:
            width += extraPadding
            originX = 0
            if para is not None:
                if para.alignment() == AppKit.NSTextAlignmentCenter:
                    originX -= width * .5
                elif para.alignment() == AppKit.NSTextAlignmentRight:
                    originX = -width

            if attributedSubstring.string()[-1] in ["\n", "\r"]:
                attributedSubstring = attributedSubstring.mutableCopy()
                attributedSubstring.deleteCharactersInRange_((rng.length - 1, 1))
            if plainText:
                substring = attributedSubstring.string()
            else:
                substring = FormattedString()
                substring.getNSObject().appendAttributedString_(attributedSubstring)

            lineX = x + originX

            if isFirstLine:
                lineY = y - originY
                box = (lineX, lineY, width, h * 2)
            else:
                lineY = y + originY + firstLineJump - h * 2
                subSetter = CoreText.CTFramesetterCreateWithAttributedString(attributedSubstring)
                subPath = Quartz.CGPathCreateMutable()
                Quartz.CGPathAddRect(subPath, None, Quartz.CGRectMake(lineX, lineY, w, h * 2))
                subFrame = CoreText.CTFramesetterCreateFrame(subSetter, (0, 0), subPath, None)
                subOrigins = CoreText.CTFrameGetLineOrigins(subFrame, (0, 1), None)
                if subOrigins:
                    subOriginY = subOrigins[0].y
                else:
                    continue

                box = (lineX, lineY - subOriginY, width, h * 2)

            boxes.append((substring, box))

        isFirstLine = False

    return boxes


class FormattedString(SVGContextPropertyMixin, ContextPropertyMixin):

    """
    FormattedString is a reusable object, if you want to draw the same over and over again.
    FormattedString objects can be drawn with the `text(txt, (x, y))` and `textBox(txt, (x, y, w, h))` methods.
    """

    _colorClass = Color
    _cmykColorClass = CMYKColor

    _textAlignMap = dict(
        center=AppKit.NSTextAlignmentCenter,
        left=AppKit.NSTextAlignmentLeft,
        right=AppKit.NSTextAlignmentRight,
        justified=AppKit.NSTextAlignmentJustified,
    )

    _textTabAlignMap = dict(
        center=AppKit.NSTextAlignmentCenter,
        left=AppKit.NSTextAlignmentLeft,
        right=AppKit.NSTextAlignmentRight,
    )

    _textUnderlineMap = dict(
        single=AppKit.NSUnderlineStyleSingle,
        thick=AppKit.NSUnderlineStyleThick,
        double=AppKit.NSUnderlineStyleDouble,
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
        fallbackFontNumber=0,
        fontSize=10,
        fontNumber=0,

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
        url=None,
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
            if isinstance(value, dict):
                value = dict(value)
            if isinstance(value, list):
                value = list(value)
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
        * `tracking`: set tracking for the given text in absolute points
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
        attributes = self._validateAttributes(kwargs, addDefaults=False)
        for key, value in attributes.items():
            self._setAttribute(key, value)
        self._setColorAttributes(attributes)

        if isinstance(txt, FormattedString):
            self._attributedString.appendAttributedString_(txt.getNSObject())
            return
        elif not isinstance(txt, (str, FormattedString)):
            raise TypeError("expected 'str' or 'FormattedString', got '%s'" % type(txt).__name__)
        attributes = {}
        attributes[AppKit.NSLigatureAttributeName] = 1  # https://github.com/typemytype/drawbot/issues/427
        if self._font:
            font = self._getNSFontWithFallback()
            coreTextFontFeatures = []
            nsFontFeatures = []  # fallback for macOS < 10.13
            if self._openTypeFeatures:
                # store openTypeFeatures in a custom attributes key
                attributes["drawbot.openTypeFeatures"] = dict(self._openTypeFeatures)
                # get existing openTypeFeatures for the font
                existingOpenTypeFeatures = openType.getFeatureTagsForFont(font)
                # sort features by their on/off state
                # set all disabled features first
                orderedOpenTypeFeatures = sorted(self._openTypeFeatures.items(), key=lambda kv: kv[1])
                for featureTag, value in orderedOpenTypeFeatures:
                    if value and featureTag not in existingOpenTypeFeatures:
                        # only warn when the feature is on and not existing for the current font
                        warnings.warn("OpenType feature '%s' not available for '%s'" % (featureTag, self._font))
                    feature = dict(CTFeatureOpenTypeTag=featureTag, CTFeatureOpenTypeValue=value)
                    coreTextFontFeatures.append(feature)
                    # The next lines are a fallback for macOS < 10.13
                    nsFontFeatureTag = featureTag
                    if not value:
                        nsFontFeatureTag = "%s_off" % featureTag
                    if nsFontFeatureTag in SFNTLayoutTypes.featureMap:
                        feature = SFNTLayoutTypes.featureMap[nsFontFeatureTag]
                        nsFontFeatures.append(feature)
                    # kern is a special case
                    if featureTag == "kern" and not value:
                        # https://developer.apple.com/documentation/uikit/nskernattributename
                        # The value 0 means kerning is disabled.
                        attributes[AppKit.NSKernAttributeName] = 0

            coreTextFontVariations = variation.getFontVariationAttributes(font, self._fontVariations)

            fontAttributes = {}
            if coreTextFontFeatures:
                fontAttributes[CoreText.kCTFontFeatureSettingsAttribute] = coreTextFontFeatures
                if macOSVersion < "10.13":
                    # fallback for macOS < 10.13:
                    fontAttributes[CoreText.NSFontFeatureSettingsAttribute] = nsFontFeatures
            if coreTextFontVariations:
                fontAttributes[CoreText.NSFontVariationAttribute] = coreTextFontVariations
            if self._fallbackFont:
                fallbackFont = getNSFontFromNameOrPath(self._fallbackFont, self._fontSize, self._fallbackFontNumber)
                if fallbackFont is not None:
                    fallbackFontDescriptor = fallbackFont.fontDescriptor()
                    fontAttributes[CoreText.NSFontCascadeListAttribute] = [fallbackFontDescriptor]
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
            # stroke width must be negative
            # Supply a negative value for NSStrokeWidthAttributeName
            # when you wish to draw a string that is both filled and stroked.
            # see https://developer.apple.com/library/content/qa/qa1531/_index.html
            # The stroke weight scales with the font size, where it matches the value
            # at 100 points. Our value should not scale with the font size, so we
            # compensate by multiplying by 100 and dividing by the font size.
            attributes[AppKit.NSStrokeWidthAttributeName] = -abs(100 * self._strokeWidth / self._fontSize)
        para = AppKit.NSMutableParagraphStyle.alloc().init()
        if self._align:
            para.setAlignment_(self._textAlignMap[self._align])
        if self._tabs:
            for tabStop in para.tabStops():
                para.removeTabStop_(tabStop)

            if len(self._tabs) < 12:
                self._tabs = list(self._tabs)
                # add tab stops if there is not enough stops...
                # the default is 12 tabs, so lets add 12 in steps of 28
                lastTabValue = self._tabs[-1][0]
                for tabIndex in range(12 - len(self._tabs)):
                    self._tabs.append((lastTabValue + 28 * (tabIndex + 1), "left"))

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
            # para.setLineSpacing_(0.0)
            # para.setLineHeightMultiple_(1)
            para.setMinimumLineHeight_(self._lineHeight)
            para.setMaximumLineHeight_(self._lineHeight)

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

        if self._tracking is not None:
            if macOSVersion < "10.12":
                attributes[AppKit.NSKernAttributeName] = self._tracking
            else:
                attributes[CoreText.kCTTrackingAttributeName] = self._tracking
        if self._baselineShift is not None:
            attributes[AppKit.NSBaselineOffsetAttributeName] = self._baselineShift
        if self._underline in self._textUnderlineMap:
            attributes[AppKit.NSUnderlineStyleAttributeName] = self._textUnderlineMap[self._underline]
        if self._url is not None:
            attributes[AppKit.NSLinkAttributeName] = AppKit.NSURL.URLWithString_(self._url)
        if self._language:
            attributes["NSLanguage"] = self._language
        attributes[AppKit.NSParagraphStyleAttributeName] = para
        txt = AppKit.NSAttributedString.alloc().initWithString_attributes_(txt, attributes)
        self._attributedString.appendAttributedString_(txt)

    def _getNSFontWithFallback(self):
        font = getNSFontFromNameOrPath(self._font, self._fontSize, self._fontNumber)
        if font is None:
            ff = self._fallbackFont
            ffNumber = self._fallbackFontNumber
            if ff is None:
                ff = _FALLBACKFONT
                ffNumber = 0
            fontNumberString = f" fontNumber={self._fontNumber}" if self._fontNumber else ""
            warnings.warn(f"font: '{self._font}'{fontNumberString} can't be found, using the fallback font '{ff}'")
            font = getNSFontFromNameOrPath(ff, self._fontSize, ffNumber)
        return font

    def __add__(self, txt):
        new = self.copy()
        if isinstance(txt, self.__class__):
            new.getNSObject().appendAttributedString_(txt.getNSObject())
        else:
            if not isinstance(txt, str):
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

    def font(self, fontNameOrPath, fontSize=None, fontNumber=0):
        """
        Set a font with the name of the font.
        If a font path is given the font will used directly.
        Optionally a `fontSize` can be set directly.
        The default font, also used as fallback font, is 'LucidaGrande'.
        The default `fontSize` is 10pt.

        The name of the font relates to the font's postscript name.

        The font name is returned, which is handy when the font was loaded
        from a path.
        """
        self._font = fontNameOrPath
        if fontSize is not None:
            self._fontSize = fontSize
        self._fontNumber = fontNumber
        font = getNSFontFromNameOrPath(fontNameOrPath, fontSize or 10, fontNumber)
        return getFontName(font)

    def fontNumber(self, fontNumber):
        self._fontNumber = fontNumber

    def fallbackFont(self, fontNameOrPath, fontNumber=0):
        """
        Set a fallback font, used whenever a glyph is not available in the normal font.
        If a font path is given the font will be installed and used directly.
        """
        fontName = None
        if fontNameOrPath is not None:
            testFont = getNSFontFromNameOrPath(fontNameOrPath, 10, fontNumber)
            if testFont is None:
                raise DrawBotError(f"Fallback font '{fontNameOrPath}' is not available")
            fontName = getFontName(fontName)
        self._fallbackFont = fontNameOrPath
        self._fallbackFontNumber = fontNumber
        return fontName

    def fallbackFontNumber(self, fontNumber):
        self._fallbackFontNumber = fontNumber

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
        Set the tracking between characters. It adds an absolute number of
        points between the characters.
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
        Underline must be `single`, `thick`, `double` or `None`.
        """
        self._underline = underline

    def url(self, url):
        """
        set the url value.
        url must be a string or `None`
        """
        self._url = url

    def openTypeFeatures(self, *args, **features):
        """
        Enable OpenType features and return the current openType features settings.

        If no arguments are given `openTypeFeatures()` will just return the current openType features settings.

        .. downloadcode:: openTypeFeaturesFormattedString.py

            size(1000, 200)
            # create an empty formatted string object
            t = FormattedString()
            # set a font
            t.font("Didot")
            # set a font size
            t.fontSize(60)
            # add some text
            t += "0123456789 Hello"
            # enable some open type features
            t.openTypeFeatures(smcp=True, onum=True)
            # add some text
            t += " 0123456789 Hello"
            # draw the formatted string
            text(t, (10, 80))
        """
        if args and features:
            raise DrawBotError("Can't combine positional arguments and keyword arguments")
        if args:
            if len(args) != 1:
                raise DrawBotError("There can only be one positional argument")
            if args[0] is not None:
                raise DrawBotError("First positional argument can only be None")
            warnings.warn("openTypeFeatures(None) is deprecated, use openTypeFeatures(resetFeatures=True) instead.")
            self._openTypeFeatures.clear()
        else:
            if features.pop("resetFeatures", False):
                self._openTypeFeatures.clear()
            self._openTypeFeatures.update(features)
        return dict(self._openTypeFeatures)

    def listOpenTypeFeatures(self, fontNameOrPath=None, fontNumber=0):
        """
        List all OpenType feature tags for the current font.

        Optionally a `fontNameOrPath` can be given. If a font path is given the font will be used directly.
        """
        if fontNameOrPath is None:
            fontNameOrPath = self._font
        font = getNSFontFromNameOrPath(fontNameOrPath, 10, fontNumber)
        return openType.getFeatureTagsForFont(font)

    def fontVariations(self, *args, **axes):
        """
        Pick a variation by axes values and return the current font variations settings.

        If no arguments are given `fontVariations()` will just return the current font variations settings.
        """
        if args and axes:
            raise DrawBotError("Can't combine positional arguments and keyword arguments")
        if args:
            if len(args) != 1:
                raise DrawBotError("There can only be one positional argument")
            if args[0] is not None:
                raise DrawBotError("First positional argument can only be None")
            warnings.warn("fontVariations(None) is deprecated, use fontVariations(resetVariations=True) instead.")
            self._fontVariations.clear()
        else:
            if axes.pop("resetVariations", False):
                self._fontVariations.clear()
            self._fontVariations.update(axes)
        defaultVariations = self.listFontVariations()
        currentVariation = {axis: data["defaultValue"] for axis, data in defaultVariations.items()}
        currentVariation.update(self._fontVariations)
        return currentVariation

    def listFontVariations(self, fontNameOrPath=None, fontNumber=0):
        """
        List all variation axes for the current font.

        Returns a dictionary with all axis tags instance with an info dictionary with the following keys: `name`, `minValue` and `maxValue`.
        For non variable fonts an empty dictionary is returned.

        Optionally a `fontNameOrPath` can be given. If a font path is given the font will be used directly.
        """
        if fontNameOrPath is None:
            fontNameOrPath = self._font
        font = getNSFontFromNameOrPath(fontNameOrPath, 10, fontNumber)
        return variation.getVariationAxesForFont(font)

    def listNamedInstances(self, fontNameOrPath=None, fontNumber=0):
        """
        List all named instances from a variable font for the current font.

        Returns a dictionary with all named instance as postscript names with their location.
        For non variable fonts an empty dictionary is returned.

        Optionally a `fontNameOrPath` can be given. If a font path is given the font will be used directly.
        """
        if fontNameOrPath is None:
            fontNameOrPath = self._font
        font = getNSFontFromNameOrPath(fontNameOrPath, 10, fontNumber)
        return variation.getNamedInstancesForFont(font)

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
            x, y, w, h = 10, 10, 500, 600

            txtIndent = 100
            txtFirstLineIndent = 200
            txtTailIndent = -100
            txtFontSize = 22

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
            t = FormattedString(fontSize=txtFontSize)
            # set alignment
            t.align("justified")
            # add text
            t += txt
            # add hard return
            t += "\\n"
            # set style for indented text
            t.fontSize(txtFontSize*.6)
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
            t.fontSize(txtFontSize)
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

        If positive, this value is the distance from the leading margin.
        If 0 or negative, it’s the distance from the trailing margin.
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

        `language()` will activate the `locl` OpenType features, if supported by the current font.
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
        new.copyContextProperties(self)
        return new

    def fontContainsCharacters(self, characters):
        """
        Return a bool if the current font contains the provided `characters`.
        Characters is a string containing one or more characters.
        """
        font = self._getNSFontWithFallback()
        if font is None:
            return False
        result, glyphs = CoreText.CTFontGetGlyphsForCharacters(font, characters, None, len(characters))
        return result

    def fontContainsGlyph(self, glyphName):
        font = self._getNSFontWithFallback()
        if font is None:
            return False
        glyph = font.glyphWithName_(glyphName)
        return bool(glyph)

    def fontFilePath(self):
        """
        Return the path to the file of the current font.
        """
        font = getNSFontFromNameOrPath(self._font, self._fontSize, self._fontNumber)
        if font is not None:
            url = CoreText.CTFontDescriptorCopyAttribute(font.fontDescriptor(), CoreText.kCTFontURLAttribute)
            if url is not None:
                return url.path()
            elif os.path.exists(self._font):
                # This happens for reloaded fonts: the font object can't
                # know its file origin, because it was loaded from data.
                return os.path.abspath(self._font)
        warnings.warn("Cannot find the path to the font '%s'." % self._font)
        return None

    def fontFileFontNumber(self):
        fontNumber = 0
        path = self.fontFilePath()
        if path is not None:
            font = getNSFontFromNameOrPath(self._font, self._fontSize, self._fontNumber)
            descriptors = getFontDescriptorsFromPath(path)
            fontNames = [d.postscriptName() for d in descriptors]
            try:
                fontNumber = fontNames.index(font.fontDescriptor().postscriptName())
            except ValueError:
                warnings.warn(f"Cannot find the fontNumber for '{self._font}'.")
        return fontNumber

    def listFontGlyphNames(self):
        """
        Return a list of glyph names supported by the current font.
        """
        from fontTools.ttLib import TTFont, TTLibError

        path = self.fontFilePath()
        if path is None:
            return []
        # load the font with fontTools
        # provide a fontNumber as lots of fonts are .ttc font files.
        # search for the res_name_or_index for .dfont files.
        res_name_or_index = None
        fontNumber = None
        ext = os.path.splitext(path)[-1].lower()
        if ext in (".ttc", ".otc"):
            fontNumber = self.fontFileFontNumber()
        elif ext == ".dfont":
            res_name_or_index = self.fontFileFontNumber() + 1
        try:
            with TTFont(path, lazy=True, fontNumber=fontNumber, res_name_or_index=res_name_or_index) as fontToolsFont:
                glyphNames = fontToolsFont.getGlyphOrder()
        except TTLibError:
            warnings.warn("Cannot read the font file for '%s' at the path '%s'" % (self._font, path))
            return []
        # remove .notdef from glyph names
        if ".notdef" in glyphNames:
            glyphNames.remove(".notdef")
        return glyphNames

    def fontAscender(self):
        """
        Returns the current font ascender, based on the current `font` and `fontSize`.
        """
        font = self._getNSFontWithFallback()
        return font.ascender()

    def fontDescender(self):
        """
        Returns the current font descender, based on the current `font` and `fontSize`.
        """
        font = self._getNSFontWithFallback()
        return font.descender()

    def fontXHeight(self):
        """
        Returns the current font x-height, based on the current `font` and `fontSize`.
        """
        font = self._getNSFontWithFallback()
        return font.xHeight()

    def fontCapHeight(self):
        """
        Returns the current font cap height, based on the current `font` and `fontSize`.
        """
        font = self._getNSFontWithFallback()
        return font.capHeight()

    def fontLeading(self):
        """
        Returns the current font leading, based on the current `font` and `fontSize`.
        """
        font = self._getNSFontWithFallback()
        return font.leading()

    def fontLineHeight(self):
        """
        Returns the current line height, based on the current `font` and `fontSize`.
        If a `lineHeight` is set, this value will be returned.
        """
        if self._lineHeight is not None:
            return self._lineHeight
        font = self._getNSFontWithFallback()
        return font.defaultLineHeightForFont()

    def appendGlyph(self, *glyphNames):
        """
        Append a glyph by his glyph name or glyph index using the current `font`.
        Multiple glyph names are possible.

        .. downloadcode:: appendGlyphFormattedString.py

            size(1300, 400)
            # create an empty formatted string object
            t = FormattedString()
            # set a font
            t.font("Menlo-Regular")
            # set a font size
            t.fontSize(300)
            # add some glyphs by glyph name
            t.appendGlyph("A", "ampersand", "Eng", "Eng.alt")
            # add some glyphs by glyph ID (this depends heavily on the font)
            t.appendGlyph(50, 51)
            # draw the formatted string
            text(t, (100, 100))

        """
        # use a non breaking space as replacement character
        baseString = chr(0xFFFD)
        font = None
        if self._font:
            font = self._getNSFontWithFallback()
        else:
            # Default font
            font = AppKit.NSFont.fontWithName_size_(_FALLBACKFONT, self._fontSize)

        # disable calt features, as this seems to be on by default
        # for both the font stored in the nsGlyphInfo as in the replacement character
        fontAttributes = {}
        coreTextFontVariations = variation.getFontVariationAttributes(font, self._fontVariations)
        if coreTextFontVariations:
            fontAttributes[CoreText.NSFontVariationAttribute] = coreTextFontVariations

        fontAttributes[CoreText.kCTFontFeatureSettingsAttribute] = [dict(CTFeatureOpenTypeTag="calt", CTFeatureOpenTypeValue=False)]
        fontDescriptor = font.fontDescriptor()
        fontDescriptor = fontDescriptor.fontDescriptorByAddingAttributes_(fontAttributes)
        font = AppKit.NSFont.fontWithDescriptor_size_(fontDescriptor, self._fontSize)

        fallbackFont = self._fallbackFont
        self._fallbackFont = None
        _openTypeFeatures = dict(self._openTypeFeatures)
        self._openTypeFeatures = dict(calt=False)
        for glyphName in glyphNames:
            if isinstance(glyphName, int):
                # glyphName is a glyph ID
                glyph = glyphName
            else:
                glyph = font.glyphWithName_(glyphName)
            if glyph:
                self.append(baseString)
                glyphInfo = AppKit.NSGlyphInfo.glyphInfoWithGlyph_forFont_baseString_(glyph, font, baseString)
                if glyphInfo is not None:
                    self._attributedString.addAttribute_value_range_(AppKit.NSGlyphInfoAttributeName, glyphInfo, (len(self) - 1, 1))
                else:
                    warnings.warn(f"font '{font.fontName()}' has no glyph with glyph ID {glyph}")
            else:
                if isinstance(glyphName, int) or glyphName == ".notdef":
                    message = "skipping '.notdef' glyph (glyph ID 0)"
                else:
                    message = "font '{fontName}' has no glyph with the name '{glyphName}'"
                warnings.warn(message.format(fontName=font.fontName(), glyphName=glyphName))

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
    saveImageOptions = []
    validateSaveImageOptions = True

    _textAlignMap = FormattedString._textAlignMap
    _textTabAlignMap = FormattedString._textTabAlignMap
    _textUnderlineMap = FormattedString._textUnderlineMap

    _colorSpaceMap = dict(
        genericRGB=AppKit.NSColorSpace.genericRGBColorSpace(),
        adobeRGB1998=AppKit.NSColorSpace.adobeRGB1998ColorSpace(),
        sRGB=AppKit.NSColorSpace.sRGBColorSpace(),
        genericGray=AppKit.NSColorSpace.genericGrayColorSpace(),
        genericGamma22Gray=AppKit.NSColorSpace.genericGamma22GrayColorSpace(),
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

    def _image(self, path, xy, alpha, pageNumber):
        pass

    def _frameDuration(self, seconds):
        pass

    def _reset(self, other=None):
        pass

    def _saveImage(self, path, options):
        pass

    def _printImage(self, pdf=None):
        pass

    def _linkURL(self, url, xywh):
        pass

    def _linkDestination(self, name, xy):
        pass

    def _linkRect(self, name, xywh):
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

    def saveImage(self, path, options):
        if not self.hasPage:
            raise DrawBotError("can't save image when no page is set")
        return self._saveImage(path, options)

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

    def qCurveTo(self, points):
        self._state.path.qCurveTo(*points)

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
        if join not in _LINEJOINSTYLESMAP:
            raise DrawBotError("lineJoin() argument must be 'bevel', 'miter' or 'round'")
        self._state.lineJoin = _LINEJOINSTYLESMAP[join]

    def lineCap(self, cap):
        if cap is None:
            self._state.lineCap = None
        if cap not in _LINECAPSTYLESMAP:
            raise DrawBotError("lineCap() argument must be 'butt', 'square' or 'round'")
        self._state.lineCap = _LINECAPSTYLESMAP[cap]

    def lineDash(self, dash):
        if dash[0] is None:
            self._state.lineDash = None
            return
        self._state.lineDash = list(dash)

    def transform(self, matrix):
        self._transform(matrix)

    def font(self, fontName, fontSize, fontNumber):
        return self._state.text.font(fontName, fontSize, fontNumber)

    def fallbackFont(self, fontName, fontNumber=0):
        self._state.text.fallbackFont(fontName, fontNumber)

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

    def url(self, value):
        self._state.text.url(value)

    def hyphenation(self, value):
        self._state.hyphenation = value

    def tabs(self, *tabs):
        self._state.text.tabs(*tabs)

    def language(self, language):
        self._state.text.language(language)

    def openTypeFeatures(self, *args, **features):
        return self._state.text.openTypeFeatures(*args, **features)

    def fontVariations(self, *args, **axes):
        return self._state.text.fontVariations(*args, **axes)

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
                    mutString.insertString_atIndex_(chr(self._softHypen), hyphenIndex)

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
            if len(subStringText) and subStringText[-1] == chr(self._softHypen):
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
                    if breakString.string()[-1] == chr(self._softHypen):
                        stringWidth += hyphenWidth
                    # found a break
                    if stringWidth <= maxLineWidth:
                        breakFound = True
                        break

                if breakFound and len(breakString.string()) > 2 and breakString.string()[-1] == chr(self._softHypen):
                    # if the break line ends with a soft hyphen
                    # add a hyphen
                    attrString.replaceCharactersInRange_withString_((rng.location + lineBreak, 0), "-")
                # remove all soft hyphens for the range of that line
                mutString.replaceOccurrencesOfString_withString_options_range_(chr(self._softHypen), "", AppKit.NSLiteralSearch, rng)
                # reset the lines, from the adjusted attribute string
                lines = self._getTypesetterLinesWithPath(attrString, path)
                # reset the justifed lines form the adjusted attributed string
                justifiedLines = self._getTypesetterLinesWithPath(self._justifyAttributedString(attrString), path)
            # next line
            i += 1
        # remove all soft hyphen
        mutString.replaceOccurrencesOfString_withString_options_range_(chr(self._softHypen), "", AppKit.NSLiteralSearch, (0, mutString.length()))
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

    def image(self, path, xy, alpha, pageNumber):
        x, y = xy
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

    def linkURL(self, url, xywh):
        x, y, w, h = xywh
        self._linkURL(url, (x, y, w, h))

    def linkDestination(self, name, xy):
        x, y = xy
        self._linkDestination(name, (x, y))

    def linkRect(self, name, xywh):
        x, y, w, h = xywh
        self._linkRect(name, (x, y, w, h))


@memoize
def getNSFontFromNameOrPath(fontNameOrPath, fontSize, fontNumber):
    if not isinstance(fontNameOrPath, (str, os.PathLike)):
        tp = type(fontNameOrPath).__name__
        raise TypeError(
            f"'fontNameOrPath' should be str or path-like, '{tp}' found"
        )
    font = _getNSFontFromNameOrPath(fontNameOrPath, fontSize, fontNumber)
    if font is None:
        warnings.warn(f"not font could be found for '{fontNameOrPath}'")
    return font


def _getNSFontFromNameOrPath(fontNameOrPath, fontSize, fontNumber):
    if fontSize is None:
        fontSize = 10
    if isinstance(fontNameOrPath, str):
        nsFont = AppKit.NSFont.fontWithName_size_(fontNameOrPath, fontSize)
        if nsFont is not None:
            return nsFont
    # load from path
    if not os.path.exists(fontNameOrPath):
        return None
    fontPath = os.path.abspath(fontNameOrPath)
    descriptors = getFontDescriptorsFromPath(fontPath)
    if not descriptors:
        return None
    if not 0 <= fontNumber < len(descriptors):
        raise IndexError(
            f"fontNumber out of range for '{fontPath}': "
            f"{fontNumber} not in range 0..{len(descriptors) - 1}"
        )
    return CoreText.CTFontCreateWithFontDescriptor(descriptors[fontNumber], fontSize, None)


#
# Cache for font descriptors that have been reloaded after a font file
# changed on disk. Keys are absolute paths to font files, values are
# (modificationTime, fontDescriptors) tuples. `fontDescriptors` is
# None when the font was used but did not have to be reloaded, and a
# list of font descriptors if the font has been reloaded before.
#
# We don't clear this cache, as the number of reloaded fonts should
# generably be within reasonable limits, and re-reloading upon every
# run (think Variable Sliders) is expensive.
#
# NOTE: It's possible to turn this into a Least Recently Used cache with
# a maximum size, using Python 3.7's insertion order preserving dict
# behavior, but it may not be worth the effort.
#
_reloadedFontDescriptors = {}


@memoize
def getFontDescriptorsFromPath(fontPath):
    modTime = os.stat(fontPath).st_mtime
    prevModTime, descriptors = _reloadedFontDescriptors.get(fontPath, (modTime, None))
    if modTime == prevModTime:
        if not descriptors:
            # Load font from disk, letting the OS handle caching and loading
            url = AppKit.NSURL.fileURLWithPath_(fontPath)
            assert url is not None
            descriptors = CoreText.CTFontManagerCreateFontDescriptorsFromURL(url)
            # Nothing was reloaded, this is the general case: do not cache the
            # descriptors globally (they are cached per newDrawing session via
            # @memoize), only store the modification time.
            _reloadedFontDescriptors[fontPath] = modTime, None
    else:
        # The font file was changed on disk since we last used it. We now load
        # it from data explicitly, bypassing any OS cache, ensuring we will see
        # the updated font.
        data = AppKit.NSData.dataWithContentsOfFile_(fontPath)
        descriptors = CoreText.CTFontManagerCreateFontDescriptorsFromData(data)
        _reloadedFontDescriptors[fontPath] = modTime, descriptors
    return descriptors


def getFontName(font):
    if font is None:
        return None
    fontName = CoreText.CTFontDescriptorCopyAttribute(font.fontDescriptor(), CoreText.kCTFontNameAttribute)
    if fontName is not None:
        fontName = str(fontName)
    return fontName
