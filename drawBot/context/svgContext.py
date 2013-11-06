import AppKit
import CoreText

import random

from xmlWriter import XMLWriter

from fontTools.misc.transform import Transform

from baseContext import BaseContext, GraphicsState

from drawBot.misc import warnings


class SVGFile(object):
    
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

class SVGGraphicsState(GraphicsState):

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
    _svgFileClass = SVGFile

    _svgTagArguments = {
        "version" : "1.1", 
        "xmlns" : "http://www.w3.org/2000/svg",
        "xmlns:xlink" : "http://www.w3.org/1999/xlink"
        }

    _svgLineJoinStylesMap = {   
                    AppKit.NSMiterLineJoinStyle : "miter",
                    AppKit.NSRoundLineJoinStyle : "round",
                    AppKit.NSBevelLineJoinStyle : "bevel"
                    }

    _svgLineCapStylesMap = {
        AppKit.NSButtLineCapStyle : "butt",
        AppKit.NSSquareLineCapStyle : "square",
        AppKit.NSRoundLineCapStyle : "round",
    }

    fileExtensions = ["svg"]

    def shadow(self, offset, blur, color):
        warnings.warn("shadow is not supported in a svg context")

    def cmykShadow(self, offset, blur, color):
        warnings.warn("shadow is not supported in a svg context")

    def linearGradient(self, startPoint=None, endPoint=None, colors=None, locations=None):
        warnings.warn("linearGradient is not supported in a svg context")

    def radialGradient(self, startPoint=None, endPoint=None, colors=None, locations=None, startRadius=0, endRadius=100):
        warnings.warn("radialGradient is not supported in a svg context")

    def _newPage(self, width, height):
        self.reset()
        self.size(width, height)
        self._svgData = self._svgFileClass()
        self._svgContext = XMLWriter(self._svgData)
        self._svgContext.begintag("svg", width=self.width, height=self.height, **self._svgTagArguments)
        self._svgContext.newline()
        self._state.transformMatrix = self._state.transformMatrix.scale(1, -1).translate(0, -self.height)

    def _saveImage(self, path):
        self._svgContext.endtag("svg")
        self._svgData.writeToFile(path) 

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
        attrString = self.attributedString(txt, align=align)
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = CoreText.CGPathCreateMutable()
        CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)

        self._save()
        self._svgBeginClipPath()
        data = self._svgDrawingAttributes()
        data["font-family"] = self._state.text.fontName
        data["font-size"] = self._state.text.fontSize
        data["transform"] = self._svgTransform(self._state.transformMatrix.translate(x, y + h).scale(1, -1))
        data["text-anchor"] = "start"

        lines = []
        
        ctLines = CoreText.CTFrameGetLines(box)
        for ctLine in ctLines:
            r = CoreText.CTLineGetStringRange(ctLine)
            line = txt[r.location:r.location+r.length]
            while line and line[-1] == " ":
                line = line[:-1]
            lines.append(line.replace("\n", ""))

        self._svgContext.begintag("text", **data)
        self._svgContext.newline()
        txt = []
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        for i, (originX, originY) in enumerate(origins):
            line = lines[i]
            self._svgContext.begintag("tspan", x=originX, y=h-originY)
            self._svgContext.newline()
            self._svgContext.write(line)
            self._svgContext.newline()
            self._svgContext.endtag("tspan")
            self._svgContext.newline()
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

    def _svgPath(self, path):
        path = path.getNSBezierPath()
        svg = ""
        for i in range(path.elementCount()):
            instruction, points = path.elementAtIndex_associatedPoints_(i)
            if instruction == AppKit.NSMoveToBezierPathElement:
                svg += "M%s,%s " %(points[0].x, points[0].y)
            elif instruction == AppKit.NSLineToBezierPathElement:
                svg += "L%s,%s " %(points[0].x, points[0].y)
            elif instruction == AppKit.NSCurveToBezierPathElement:
                svg += "C%s,%s,%s,%s,%s,%s " %(points[0].x, points[0].y, points[1].x, points[1].y, points[2].x, points[2].y)
            elif instruction == AppKit.NSClosePathBezierPathElement:
                svg += "Z "
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
        return data

    def _svgFillColor(self):
        if self._state.fillColor:
            c = self._state.fillColor.getNSObject()
            return "rgba(%s,%s,%s,%s)" % (int(255*c.redComponent()), int(255*c.greenComponent()), int(255*c.blueComponent()), c.alphaComponent())
        else:
            return "none"
    
    def _svgStrokeColor(self):
        if self._state.strokeColor:
            c = self._state.strokeColor.getNSObject()
            return "rgba(%s,%s,%s,%s)" % (int(255*c.redComponent()), int(255*c.greenComponent()), int(255*c.blueComponent()), c.alphaComponent())
        else:
            return "none"
