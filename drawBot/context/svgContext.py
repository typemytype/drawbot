import AppKit
import CoreText

import os

import random

from xmlWriter import XMLWriter

from fontTools.misc.transform import Transform

from baseContext import BaseContext, GraphicsState, Shadow, Color, FormattedString, Gradient

from drawBot.misc import warnings


# simple file object


class SVGFile(object):

    optimize = False

    def __init__(self):
        self._svgdata = []

    def write(self, value):
        self._svgdata.append(value)

    def writeToFile(self, path):
        data = self.read()
        f = open(path, "w")
        f.write(data)
        f.close()

    def read(self):
        return "".join(self._svgdata)

    def close(self):
        pass


# subclass some object to add some svg api


class SVGColor(Color):

    def svgColor(self):
        c = self.getNSObject()
        if c:
            return "rgba(%s,%s,%s,%s)" % (int(255*c.redComponent()), int(255*c.greenComponent()), int(255*c.blueComponent()), c.alphaComponent())
        return "none"


class SVGGradient(Gradient):

    _colorClass = SVGColor

    def __init__(self, *args, **kwargs):
        super(SVGGradient, self).__init__(*args, **kwargs)
        self.tagID = id(self)

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
            stopData = {"offset": position, "stop-color": color.svgColor()}
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
            stopData = {"offset": position, "stop-color": color.svgColor()}
            ctx.simpletag("stop", **stopData)
            ctx.newline()
        ctx.endtag("radialGradient")
        ctx.newline()


class SVGShadow(Shadow):

    _colorClass = SVGColor

    def __init__(self, *args, **kwargs):
        super(SVGShadow, self).__init__(*args, **kwargs)
        self.tagID = id(self)

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
        colorData = {"flood-color": self.color.svgColor()}
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

    _svgFileClass = SVGFile

    _svgTagArguments = {
        "version": "1.1",
        "xmlns": "http://www.w3.org/2000/svg",
        "xmlns:xlink": "http://www.w3.org/1999/xlink"
        }

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

    fileExtensions = ["svg"]

    def __init__(self):
        super(SVGContext, self).__init__()
        self._pages = []

    # not supported in a svg context

    def openTypeFeatures(self, *args, **features):
        warnings.warn("openTypeFeatures is not supported in a svg context")

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

    def _newPage(self, width, height):
        if hasattr(self, "_svgContext"):
            self._svgContext.endtag("svg")
        self.reset()
        self.size(width, height)
        self._svgData = self._svgFileClass()
        self._pages.append(self._svgData)
        self._svgContext = XMLWriter(self._svgData, encoding="utf-8")
        self._svgContext.width = self.width
        self._svgContext.height = self.height
        self._svgContext.begintag("svg", width=self.width, height=self.height, **self._svgTagArguments)
        self._svgContext.newline()
        self._state.transformMatrix = self._state.transformMatrix.scale(1, -1).translate(0, -self.height)

    def _saveImage(self, path, multipage):
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
            data["transform"] = self._svgTransform(self._state.transformMatrix)
            if self._state.shadow is not None:
                data["filter"] = "url(#%s)" % self._state.shadow.tagID
            if self._state.gradient is not None:
                data["fill"] = "url(#%s)" % self._state.gradient.tagID
            self._svgContext.simpletag("path", **data)
            self._svgContext.newline()
            self._svgEndClipPath()

    def _clipPath(self):
        uniqueID = self._getUniqueID()
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

    def _textBox(self, txt, (x, y, w, h), align):
        canDoGradients = not isinstance(txt, FormattedString)
        if align == "justified":
            warnings.warn("justified text is not supported in a svg context")
        attrString = self.attributedString(txt, align=align)
        if self._state.text.hyphenation:
            attrString = self.hyphenateAttributedString(attrString, w)
        txt = attrString.string()

        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = CoreText.CGPathCreateMutable()
        CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)

        self._svgBeginClipPath()
        defaultData = self._svgDrawingAttributes()

        data = {
            "text-anchor": "start"
            }
        if self._state.shadow is not None:
            data["filter"] = "url(#%s_flipped)" % self._state.shadow.tagID
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
                attributes = CoreText.CTRunGetAttributes(ctRun)
                font = attributes.get(AppKit.NSFontAttributeName)
                fillColor = attributes.get(AppKit.NSForegroundColorAttributeName)
                strokeColor = attributes.get(AppKit.NSStrokeColorAttributeName)
                strokeWidth = attributes.get(AppKit.NSStrokeWidthAttributeName, self._state.strokeWidth)

                fontName = font.fontName()
                fontSize = font.pointSize()

                spanData = dict(defaultData)
                spanData["fill"] = self._colorClass(fillColor).svgColor()
                spanData["stroke"] = self._colorClass(strokeColor).svgColor()
                spanData["stroke-width"] = strokeWidth
                spanData["font-family"] = fontName
                spanData["font-size"] = fontSize

                if canDoGradients and self._state.gradient is not None:
                    spanData["fill"] = "url(#%s_flipped)" % self._state.gradient.tagID

                self._save()

                r = CoreText.CTRunGetStringRange(ctRun)
                runTxt = txt.substringWithRange_((r.location, r.length))
                while runTxt and runTxt[-1] == " ":
                    runTxt = runTxt[:-1]
                runTxt = runTxt.replace("\n", "")
                runTxt = runTxt.encode("utf-8")

                runPos = CoreText.CTRunGetPositions(ctRun, (0, 1), None)
                runX = runY = 0
                if runPos:
                    runX = runPos[0].x
                    runY = runPos[0].y

                spanData["x"] = originX + runX + x
                spanData["y"] = self.height - y - originY - runY
                self._svgContext.begintag("tspan", **spanData)
                self._svgContext.newline()
                self._svgContext.write(runTxt)
                self._svgContext.newline()
                self._svgContext.endtag("tspan")
                self._svgContext.newline()
                self._restore()

        self._svgContext.endtag("text")
        self._svgContext.newline()
        self._svgEndClipPath()

    def _image(self, path, (x, y), alpha):
        self._svgBeginClipPath()
        if path.startswith("http"):
            url = AppKit.NSURL.URLWithString_(path)
        else:
            url = AppKit.NSURL.fileURLWithPath_(path)
        im = AppKit.NSImage.alloc().initByReferencingURL_(url)
        w, h = im.size()
        data = dict()
        data["x"] = 0
        data["y"] = 0
        data["width"] = w
        data["height"] = h
        data["opacity"] = alpha
        data["transform"] = self._svgTransform(self._state.transformMatrix.translate(x, y + h).scale(1, -1))
        data["xlink:href"] = path
        self._svgContext.simpletag("image", **data)
        self._svgContext.newline()
        self._svgEndClipPath()

    def _transform(self, transform):
        self._state.transformMatrix = self._state.transformMatrix.transform(transform)

    # helpers

    def _getUniqueID(self):
        b = [chr(random.randrange(256)) for i in range(16)]
        i = long(('%02x'*16) % tuple(map(ord, b)), 16)
        return '%032x' % i

    def _svgTransform(self, transform):
        return "matrix(%s)" % (",".join([str(s) for s in transform]))

    def _svgPath(self, path, transformMatrix=None):
        path = path.getNSBezierPath()
        if transformMatrix:
            path = path.copy()
            aT = AppKit.NSAffineTransform.transform()
            aT.setTransformStruct_(transformMatrix[:])
            path.transformUsingAffineTransform_(aT)
        svg = ""
        lastPoint = None
        for i in range(path.elementCount()):
            instruction, points = path.elementAtIndex_associatedPoints_(i)
            if instruction == AppKit.NSMoveToBezierPathElement:
                svg += "M%.4g,%.4g" % (points[0].x, points[0].y)
                lastPoint = points[0]
            elif instruction == AppKit.NSLineToBezierPathElement:
                svg += "l%.4g,%.4g" % (points[0].x - lastPoint.x, points[0].y - lastPoint.y)
                lastPoint = points[0]
            elif instruction == AppKit.NSCurveToBezierPathElement:
                svg += "c%.4g,%.4g,%.4g,%.4g,%.4g,%.4g" % (points[0].x - lastPoint.x, points[0].y - lastPoint.y, points[1].x - lastPoint.x, points[1].y - lastPoint.y, points[2].x - lastPoint.x, points[2].y - lastPoint.y)
                lastPoint = points[2]
            elif instruction == AppKit.NSClosePathBezierPathElement:
                svg += "Z"
        svg = svg.replace(",-", "-")
        return svg

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
        data["fill"] = self._svgFillColor()
        data["stroke"] = self._svgStrokeColor()
        data["stroke-width"] = self._state.strokeWidth
        data["stroke-dasharray"] = "none"
        if self._state.lineDash:
            data["stroke-dasharray"] = ",".join([str(i) for i in self._state.lineDash])
        data["stroke-linejoin"] = "inherit"
        if self._state.lineJoin in self._svgLineJoinStylesMap:
            data["stroke-linejoin"] = self._svgLineJoinStylesMap[self._state.lineJoin]
        data["stroke-linecap"] = "inherit"
        if self._state.lineCap in self._svgLineCapStylesMap:
            data["stroke-linecap"] = self._svgLineCapStylesMap[self._state.lineCap]
        if self._state.blendMode is not None:
            data["style"] = "mix-blend-mode: %s;" % self._state.blendMode
        return data

    def _svgFillColor(self):
        if self._state.fillColor:
            return self._state.fillColor.svgColor()
        else:
            return "none"

    def _svgStrokeColor(self):
        if self._state.strokeColor:
            return self._state.strokeColor.svgColor()
        else:
            return "none"
