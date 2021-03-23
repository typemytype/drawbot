import AppKit
import CoreText

import os
import base64

from fontTools.misc.xmlWriter import XMLWriter

from fontTools.misc.transform import Transform

from .tools.openType import getFeatureTagsForFontAttributes
from .baseContext import BaseContext, GraphicsState, Shadow, Color, Gradient, BezierPath, FormattedString
from .imageContext import _makeBitmapImageRep

from drawBot.misc import warnings, formatNumber


class _UniqueIDGenerator(object):

    def __init__(self, prefix):
        self._prefix = prefix
        self._intGenerator = self._intGeneratorFunc()

    def gen(self):
        return "%s%s" % (self._prefix, next(self._intGenerator))

    @staticmethod
    def _intGeneratorFunc():
        i = 1
        while True:
            yield i
            i += 1


# simple file object


class SVGFile(object):

    optimize = False

    def __init__(self):
        self._svgdata = []

    def write(self, value):
        self._svgdata.append(value)

    def writeToFile(self, path):
        data = self.read()
        f = open(path, "wb")
        f.write(data)
        f.close()

    def read(self):
        return b"".join(self._svgdata)

    def close(self):
        pass


# subclass some object to add some svg api


class SVGColor(Color):

    def svgColor(self):
        c = self.getNSObject()
        if c:
            if c.numberOfComponents() == 2:
                # gray number
                r = g = b = int(255 * c.whiteComponent())
            else:
                r = int(255 * c.redComponent())
                g = int(255 * c.greenComponent())
                b = int(255 * c.blueComponent())
            a = c.alphaComponent()
            return "rgb(%s,%s,%s)" % (r, g, b), a
        return None


class SVGGradient(Gradient):

    _colorClass = SVGColor
    _idGenerator = _UniqueIDGenerator("gradient")

    def __init__(self, *args, **kwargs):
        super(SVGGradient, self).__init__(*args, **kwargs)
        self.tagID = self._idGenerator.gen()

    def copy(self):
        new = super(SVGShadow, self).copy()
        new.tagID = self.tagID
        return new

    def writeDefs(self, ctx):
        ctx.begintag("defs")
        ctx.newline()
        self._writeFilter(ctx)
        ctx.endtag("defs")
        ctx.newline()

    def _writeFilter(self, ctx):
        if self.gradientType == "linear":
            self._writeLinear(ctx)
            self._writeLinear(ctx, flipped=True)
        elif self.gradientType == "radial":
            self._writeRadial(ctx)
            self._writeRadial(ctx, flipped=True)

    def _writeLinear(self, ctx, flipped=False):
        x1, y1 = self.start
        x2, y2 = self.end
        tagID = self.tagID
        if flipped:
            tagID = "%s_flipped" % tagID
            y1 = ctx.height - y1
            y2 = ctx.height - y2
        ctx.begintag("linearGradient", id=tagID, x1=x1, y1=y1, x2=x2, y2=y2, gradientUnits="userSpaceOnUse")
        ctx.newline()
        for i, color in enumerate(self.colors):
            position = self.positions[i]
            c, a = color.svgColor()
            stopData = {"offset": position, "stop-color": c}
            if a != 1:
                stopData["stop-opacity"] = a
            ctx.simpletag("stop", **stopData)
            ctx.newline()
        ctx.endtag("linearGradient")
        ctx.newline()

    def _writeRadial(self, ctx, flipped=False):
        x1, y1 = self.start
        x2, y2 = self.end
        tagID = self.tagID
        if flipped:
            tagID = "%s_flipped" % tagID
            y1 = ctx.height - y1
            y2 = ctx.height - y2
        ctx.begintag("radialGradient", id=tagID, cx=x2, cy=y2, r=self.endRadius, fx=x1, fy=y1, gradientUnits="userSpaceOnUse")
        ctx.newline()
        for i, color in enumerate(self.colors):
            position = self.positions[i]
            c, a = color.svgColor()
            stopData = {"offset": position, "stop-color": c}
            if a != 1:
                stopData["stop-opacity"] = a
            ctx.simpletag("stop", **stopData)
            ctx.newline()
        ctx.endtag("radialGradient")
        ctx.newline()


class SVGShadow(Shadow):

    _colorClass = SVGColor
    _idGenerator = _UniqueIDGenerator("shadow")

    def __init__(self, *args, **kwargs):
        super(SVGShadow, self).__init__(*args, **kwargs)
        self.tagID = self._idGenerator.gen()

    def copy(self):
        new = super(SVGShadow, self).copy()
        new.tagID = self.tagID
        return new

    def writeDefs(self, ctx):
        ctx.begintag("defs")
        ctx.newline()
        self._writeFilter(ctx)
        self._writeFilter(ctx, flipped=True)
        ctx.endtag("defs")
        ctx.newline()

    def _writeFilter(self, ctx, flipped=False):
        tagID = self.tagID
        if flipped:
            tagID = "%s_flipped" % tagID
        ctx.begintag("filter", id=tagID, x="-500%", y="-500%", width="1000%", height="1000%")
        ctx.newline()
        if self.blur < 0:
            self.blur = 0
        blurData = {"in": "SourceAlpha", "stdDeviation": "%f" % self.blur}
        ctx.simpletag("feGaussianBlur", **blurData)
        ctx.newline()
        dx, dy = self.offset
        if flipped:
            dy *= -1
        offsetData = {"dx": dx, "dy": dy, "result": "offsetblur"}
        ctx.simpletag("feOffset", **offsetData)
        ctx.newline()
        c, a = self.color.svgColor()
        colorData = {"flood-color": c}
        if a != 1:
            colorData["flood-opacity"] = a
        ctx.simpletag("feFlood", **colorData)
        ctx.newline()
        ctx.simpletag("feComposite", in2="offsetblur", operator="in")
        ctx.newline()
        ctx.begintag("feMerge")
        ctx.newline()
        ctx.simpletag("feMergeNode")
        ctx.newline()
        feMergeNodeData = {"in": "SourceGraphic"}
        ctx.simpletag("feMergeNode", **feMergeNodeData)
        ctx.newline()
        ctx.endtag("feMerge")
        ctx.newline()
        ctx.endtag("filter")
        ctx.newline()


class SVGGraphicsState(GraphicsState):

    _colorClass = SVGColor

    def __init__(self):
        super(SVGGraphicsState, self).__init__()
        self.transformMatrix = Transform(1, 0, 0, 1, 0, 0)
        self.clipPathID = None

    def copy(self):
        new = super(SVGGraphicsState, self).copy()
        new.transformMatrix = Transform(*self.transformMatrix[:])
        new.clipPathID = self.clipPathID
        return new


class SVGContext(BaseContext):

    _graphicsStateClass = SVGGraphicsState
    _shadowClass = SVGShadow
    _colorClass = SVGColor
    _gradientClass = SVGGradient
    _clipPathIDGenerator = _UniqueIDGenerator("clip")

    _svgFileClass = SVGFile

    _svgTagArguments = [
        ("version", "1.1"),
        ("xmlns", "http://www.w3.org/2000/svg"),
        ("xmlns:xlink", "http://www.w3.org/1999/xlink")
    ]

    _svgLineJoinStylesMap = {
        AppKit.NSMiterLineJoinStyle: "miter",
        AppKit.NSRoundLineJoinStyle: "round",
        AppKit.NSBevelLineJoinStyle: "bevel"
    }

    _svgLineCapStylesMap = {
        AppKit.NSButtLineCapStyle: "butt",
        AppKit.NSSquareLineCapStyle: "square",
        AppKit.NSRoundLineCapStyle: "round",
    }

    _svgUnderlineStylesMap = {
        AppKit.NSUnderlineStyleSingle: "",
        AppKit.NSUnderlineStyleThick: "",
        AppKit.NSUnderlineStyleDouble: "double",
    }

    indentation = " "
    fileExtensions = ["svg"]
    saveImageOptions = [
        ("multipage", "Output a numbered svg file for each page or frame in the document."),
    ]

    def __init__(self):
        super(SVGContext, self).__init__()
        self._pages = []

    # not supported in a svg context

    def cmykFill(self, c, m, y, k, a=1):
        warnings.warn("cmykFill is not supported in a svg context")

    def cmykStroke(self, c, m, y, k, a=1):
        warnings.warn("cmykStroke is not supported in a svg context")

    def cmykLinearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        warnings.warn("cmykLinearGradient is not supported in a svg context")

    def cmykRadialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        warnings.warn("cmykRadialGradient is not supported in a svg context")

    def cmykShadow(self, offset, blur, color):
        warnings.warn("cmykShadow is not supported in a svg context")

    # svg overwrites

    def shadow(self, offset, blur, color):
        super(SVGContext, self).shadow(offset, blur, color)
        if self._state.shadow is not None:
            self._state.shadow.writeDefs(self._svgContext)

    def linearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        super(SVGContext, self).linearGradient(startPoint, endPoint, colors, locations)
        if self._state.gradient is not None:
            self._state.gradient.writeDefs(self._svgContext)

    def radialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        super(SVGContext, self).radialGradient(startPoint, endPoint, colors, locations, startRadius, endRadius)
        if startRadius != 0:
            warnings.warn("radialGradient will clip the startRadius to '0' in a svg context.")
        if self._state.gradient is not None:
            self._state.gradient.writeDefs(self._svgContext)

    # svg

    def _reset(self, other=None):
        self._embeddedFonts = set()
        self._embeddedImages = dict()

    def _newPage(self, width, height):
        if hasattr(self, "_svgContext"):
            self._svgContext.endtag("svg")
        self.reset()
        self.size(width, height)
        self._svgData = self._svgFileClass()
        self._pages.append(self._svgData)
        self._svgContext = XMLWriter(self._svgData, encoding="utf-8", indentwhite=self.indentation)
        self._svgContext.width = self.width
        self._svgContext.height = self.height
        attrs = [('width', self.width), ('height', self.height), ('viewBox', f"0 0 {self.width} {self.height}")]
        self._svgContext.begintag("svg", attrs + self._svgTagArguments)
        self._svgContext.newline()
        self._state.transformMatrix = self._state.transformMatrix.scale(1, -1).translate(0, -self.height)

    def _saveImage(self, path, options):
        multipage = options.get("multipage")
        if multipage is None:
            multipage = False
        self._svgContext.endtag("svg")
        fileName, fileExt = os.path.splitext(path)
        firstPage = 0
        pageCount = len(self._pages)
        pathAdd = "_1"
        if not multipage:
            firstPage = pageCount - 1
            pathAdd = ""
        for index in range(firstPage, pageCount):
            page = self._pages[index]
            svgPath = fileName + pathAdd + fileExt
            page.writeToFile(svgPath)
            pathAdd = "_%s" % (index + 2)

    def _save(self):
        pass

    def _restore(self):
        pass

    def _drawPath(self):
        if self._state.path:
            self._svgBeginClipPath()
            data = self._svgDrawingAttributes()
            data["d"] = self._svgPath(self._state.path)
            if self._state.path.svgID:
                data["id"] = self._state.path.svgID
            if self._state.path.svgClass:
                data["class"] = self._state.path.svgClass
            data["transform"] = self._svgTransform(self._state.transformMatrix)
            if self._state.shadow is not None:
                data["filter"] = "url(#%s)" % self._state.shadow.tagID
            if self._state.gradient is not None:
                data["fill"] = "url(#%s)" % self._state.gradient.tagID
            if self._state.path.svgLink:
                self._svgContext.begintag("a", **{"xlink:href": self._state.path.svgLink})
                self._svgContext.newline()
            self._svgContext.simpletag("path", **data)
            self._svgContext.newline()
            if self._state.path.svgLink:
                self._svgContext.endtag("a")
                self._svgContext.newline()
            self._svgEndClipPath()

    def _clipPath(self):
        uniqueID = self._clipPathIDGenerator.gen()
        self._svgContext.begintag("clipPath", id=uniqueID)
        self._svgContext.newline()
        data = dict()
        data["d"] = self._svgPath(self._state.path)
        data["transform"] = self._svgTransform(self._state.transformMatrix)
        data["clip-rule"] = "evenodd"
        self._svgContext.simpletag("path", **data)
        self._svgContext.newline()
        self._svgContext.endtag("clipPath")
        self._svgContext.newline()
        self._state.clipPathID = uniqueID

    def _textBox(self, rawTxt, box, align):
        path, (x, y) = self._getPathForFrameSetter(box)
        canDoGradients = True
        if align == "justified":
            warnings.warn("justified text is not supported in a svg context")
        attrString = self.attributedString(rawTxt, align=align)
        if self._state.hyphenation:
            attrString = self.hyphenateAttributedString(attrString, path)
        txt = attrString.string()
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)

        self._svgBeginClipPath()
        defaultData = self._svgDrawingAttributes()

        data = {
            "text-anchor": "start",
            "transform": self._svgTransform(self._state.transformMatrix.translate(x, y + self.height).scale(1, -1))
        }
        if self._state.shadow is not None:
            data["filter"] = "url(#%s_flipped)" % self._state.shadow.tagID
        if isinstance(rawTxt, FormattedString):
            if rawTxt.svgID:
                data["id"] = rawTxt.svgID
            if rawTxt.svgClass:
                data["class"] = rawTxt.svgClass
            if rawTxt.svgLink:
                self._svgContext.begintag("a", **{"xlink:href": rawTxt.svgLink})
                self._svgContext.newline()
        self._svgContext.begintag("text", **data)
        self._svgContext.newline()

        ctLines = CoreText.CTFrameGetLines(box)
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        for i, (originX, originY) in enumerate(origins):
            ctLine = ctLines[i]
            # bounds = CoreText.CTLineGetImageBounds(ctLine, self._pdfContext)
            # if bounds.size.width == 0:
            #     continue
            ctRuns = CoreText.CTLineGetGlyphRuns(ctLine)
            for ctRun in ctRuns:
                stringRange = CoreText.CTRunGetStringRange(ctRun)
                attributes = CoreText.CTRunGetAttributes(ctRun)
                font = attributes.get(AppKit.NSFontAttributeName)
                fontDescriptor = font.fontDescriptor()
                fillColor = attributes.get(AppKit.NSForegroundColorAttributeName)
                strokeColor = attributes.get(AppKit.NSStrokeColorAttributeName)
                strokeWidth = attributes.get(AppKit.NSStrokeWidthAttributeName, self._state.strokeWidth)
                baselineShift = attributes.get(AppKit.NSBaselineOffsetAttributeName, 0)
                openTypeFeatures = attributes.get("drawbot.openTypeFeatures")
                underline = attributes.get(AppKit.NSUnderlineStyleAttributeName)
                url = attributes.get(AppKit.NSLinkAttributeName)

                fontName = font.fontName()
                fontSize = font.pointSize()
                fontFallbacks = [fallbackFont.postscriptName() for fallbackFont in fontDescriptor.get(CoreText.NSFontCascadeListAttribute, [])]
                fontNames = ", ".join([fontName] + fontFallbacks)

                style = dict()
                spanData = dict(defaultData)
                fill = self._colorClass(fillColor).svgColor()
                if fill:
                    c, a = fill
                    spanData["fill"] = c
                    if a != 1:
                        spanData["fill-opacity"] = a
                stroke = self._colorClass(strokeColor).svgColor()
                if stroke:
                    c, a = stroke
                    spanData["stroke"] = c
                    if a != 1:
                        spanData["stroke-opacity"] = a
                    spanData["stroke-width"] = formatNumber(abs(strokeWidth) * .5)
                spanData["font-family"] = fontNames
                spanData["font-size"] = formatNumber(fontSize)

                if openTypeFeatures:
                    style["font-feature-settings"] = self._svgStyleOpenTypeFeatures(openTypeFeatures)

                if canDoGradients and self._state.gradient is not None:
                    spanData["fill"] = "url(#%s_flipped)" % self._state.gradient.tagID

                if underline is not None:
                    style["text-decoration"] = "underline"
                    underlineStyle = self._svgUnderlineStylesMap.get(underline)
                    if underlineStyle:
                        style["text-decoration-style"] = underlineStyle

                if style:
                    spanData["style"] = self._svgStyle(**style)
                self._save()

                runTxt = txt.substringWithRange_((stringRange.location, stringRange.length))
                while runTxt and runTxt[-1] == " ":
                    runTxt = runTxt[:-1]
                runTxt = runTxt.replace("\n", "")
                runTxt = runTxt.encode("utf-8")

                runPos = CoreText.CTRunGetPositions(ctRun, (0, 1), None)
                runX = runY = 0
                if runPos:
                    runX = runPos[0].x
                    runY = runPos[0].y

                spanData["x"] = formatNumber(originX + runX)
                spanData["y"] = formatNumber(self.height - originY - runY + baselineShift)
                if url is not None:
                    self._svgContext.begintag("a", href=url.absoluteString())
                    self._svgContext.newline()
                self._svgContext.begintag("tspan", **spanData)
                self._svgContext.newline()
                self._svgContext.write(runTxt)
                self._svgContext.newline()
                self._svgContext.endtag("tspan")
                self._svgContext.newline()
                if url is not None:
                    self._svgContext.endtag("a")
                    self._svgContext.newline()
                self._restore()

        self._svgContext.endtag("text")
        self._svgContext.newline()
        if isinstance(rawTxt, FormattedString) and rawTxt.svgLink:
            self._svgContext.endtag("a")
            self._svgContext.newline()
        self._svgEndClipPath()

    def _image(self, path, xy, alpha, pageNumber):
        # todo:
        # support embedding of images when the source is not a path but
        # a nsimage or a pdf / gif with a pageNumber
        x, y = xy
        self._svgBeginClipPath()
        if path.startswith("http"):
            url = AppKit.NSURL.URLWithString_(path)
        else:
            url = AppKit.NSURL.fileURLWithPath_(path)
        image = AppKit.NSImage.alloc().initByReferencingURL_(url)
        width, height = image.size()

        if path not in self._embeddedImages:
            # get a unique id for the image
            imageID = "image_%s" % (len(self._embeddedImages) + 1)
            # store it
            self._embeddedImages[path] = imageID
            _, ext = os.path.splitext(path)
            mimeSubtype = ext[1:].lower()  # remove the dot, make lowercase
            if mimeSubtype == "jpg":
                mimeSubtype = "jpeg"
            if mimeSubtype not in ("png", "jpeg"):
                # the image is not a png or a jpeg
                # convert it to a png
                mimeSubtype = "png"
                imageRep = _makeBitmapImageRep(image)
                imageData = imageRep.representationUsingType_properties_(AppKit.NSPNGFileType, None)
            else:
                imageData = AppKit.NSData.dataWithContentsOfURL_(url).bytes()

            defData = [
                ("id", imageID),
                ("width", width),
                ("height", height),
                ("xlink:href", "data:image/%s;base64,%s" % (mimeSubtype, base64.b64encode(imageData).decode("ascii")))
            ]
            self._svgContext.begintag("defs")
            self._svgContext.newline()
            self._svgContext.simpletag("image", defData)
            self._svgContext.newline()
            self._svgContext.endtag("defs")
            self._svgContext.newline()
        else:
            imageID = self._embeddedImages[path]

        data = [
            ("x", 0),
            ("y", 0),
            ("opacity", alpha),
            ("transform", self._svgTransform(self._state.transformMatrix.translate(x, y + height).scale(1, -1))),
            ("xlink:href", "#%s" % imageID)
        ]
        self._svgContext.simpletag("use", data)
        self._svgContext.newline()
        self._svgEndClipPath()

    def _transform(self, transform):
        self._state.transformMatrix = self._state.transformMatrix.transform(transform)

    # helpers

    def _svgTransform(self, transform):
        return "matrix(%s)" % (",".join([repr(s) for s in transform]))

    def _svgPath(self, path, transformMatrix=None):
        path = path.getNSBezierPath()
        if transformMatrix:
            path = path.copy()
            aT = AppKit.NSAffineTransform.transform()
            aT.setTransformStruct_(transformMatrix[:])
            path.transformUsingAffineTransform_(aT)
        svg = ""
        for i in range(path.elementCount()):
            instruction, points = path.elementAtIndex_associatedPoints_(i)
            if instruction == AppKit.NSMoveToBezierPathElement:
                svg += "M%s,%s " % (formatNumber(points[0].x), formatNumber(points[0].y))
                previousPoint = points[-1]
            elif instruction == AppKit.NSLineToBezierPathElement:
                x = points[0].x - previousPoint.x
                y = points[0].y - previousPoint.y
                svg += "l%s,%s " % (formatNumber(x), formatNumber(y))
                previousPoint = points[-1]
            elif instruction == AppKit.NSCurveToBezierPathElement:
                offx1 = points[0].x - previousPoint.x
                offy1 = points[0].y - previousPoint.y
                offx2 = points[1].x - previousPoint.x
                offy2 = points[1].y - previousPoint.y
                x = points[2].x - previousPoint.x
                y = points[2].y - previousPoint.y
                svg += "c%s,%s,%s,%s,%s,%s " % (formatNumber(offx1), formatNumber(offy1), formatNumber(offx2), formatNumber(offy2), formatNumber(x), formatNumber(y))
                previousPoint = points[-1]
            elif instruction == AppKit.NSClosePathBezierPathElement:
                svg += "Z "
        return svg.strip()

    def _svgBeginClipPath(self):
        if self._state.clipPathID:
            data = dict()
            data["clip-path"] = "url(#%s)" % self._state.clipPathID
            self._svgContext.begintag("g", **data)
            self._svgContext.newline()

    def _svgEndClipPath(self):
        if self._state.clipPathID:
            self._svgContext.endtag("g")
            self._svgContext.newline()

    def _svgDrawingAttributes(self):
        data = dict()
        fill = self._svgFillColor()
        if fill:
            c, a = fill
            data["fill"] = c
            if a != 1:
                data["fill-opacity"] = a
        else:
            data["fill"] = "none"
        stroke = self._svgStrokeColor()
        if stroke:
            c, a = stroke
            data["stroke"] = c
            if a != 1:
                data["stroke-opacity"] = a
            data["stroke-width"] = formatNumber(abs(self._state.strokeWidth))
        if self._state.lineDash:
            data["stroke-dasharray"] = ",".join([str(i) for i in self._state.lineDash])
        if self._state.lineJoin in self._svgLineJoinStylesMap:
            data["stroke-linejoin"] = self._svgLineJoinStylesMap[self._state.lineJoin]
        if self._state.lineCap in self._svgLineCapStylesMap:
            data["stroke-linecap"] = self._svgLineCapStylesMap[self._state.lineCap]
        return data

    def _svgFillColor(self):
        if self._state.fillColor:
            return self._state.fillColor.svgColor()
        return None

    def _svgStrokeColor(self):
        if self._state.strokeColor:
            return self._state.strokeColor.svgColor()
        return None

    def _svgStyleOpenTypeFeatures(self, featureTags):
        return ", ".join(["'%s' %s" % (tag, int(value)) for tag, value in featureTags.items()])

    def _svgStyle(self, **kwargs):
        style = []
        if self._state.blendMode is not None:
            style.append("mix-blend-mode: %s;" % self._state.blendMode)
        for key, value in sorted(kwargs.items()):
            style.append("%s: %s;" % (key, value))
        return " ".join(style)

    def _linkURL(self, url, xywh):
        x, y, w, h = xywh
        rectData = dict(
            x=x,
            y=self.height-y-h,
            width=w,
            height=h,
            fill="transparent",
        )
        self._svgContext.begintag("a", href=url)
        self._svgContext.newline()
        self._svgContext.simpletag('rect', **rectData)
        self._svgContext.newline()
        self._svgContext.endtag("a")
        self._svgContext.newline()
