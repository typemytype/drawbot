import AppKit
import CoreText
import Quartz

import os

from baseContext import BaseContext, FormattedString
from drawBot.misc import DrawBotError

class PDFContext(BaseContext):

    fileExtensions = ["pdf"]

    def __init__(self):
        super(PDFContext, self).__init__()
        self._hasContext = False
        self._cachedImages = {}

    def _newPage(self, width, height):
        self.size(width, height)
        mediaBox = Quartz.CGRectMake(0, 0, self.width, self.height)

        if self._hasContext:
            # reset the context
            self.reset()
            # add a new page
            Quartz.CGContextEndPage(self._pdfContext)
            Quartz.CGContextBeginPage(self._pdfContext, mediaBox)
        else:
            # create a new pdf document
            self._pdfData = Quartz.CFDataCreateMutable(None, 0)
            dataConsumer = Quartz.CGDataConsumerCreateWithCFData(self._pdfData)
            self._pdfContext = Quartz.CGPDFContextCreate(dataConsumer, mediaBox, None)
            Quartz.CGContextBeginPage(self._pdfContext, mediaBox)
            self._hasContext = True

    def _closeContext(self):
        Quartz.CGContextEndPage(self._pdfContext)
        Quartz.CGPDFContextClose(self._pdfContext)
        self._hasContext = False

    def _saveImage(self, path, multipage):
        self._closeContext()
        self._writeDataToFile(self._pdfData, path, multipage)
        self._pdfContext = None
        self._pdfData = None

    def _writeDataToFile(self, data, path, multipage):
        if multipage is None:
            multipage = True
        if not multipage:
            pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
            page = pdfDocument.pageAtIndex_(pdfDocument.pageCount()-1)
            data = page.dataRepresentation()
        data.writeToFile_atomically_(path, True)

    def _save(self):
        Quartz.CGContextSaveGState(self._pdfContext)

    def _restore(self):
        Quartz.CGContextRestoreGState(self._pdfContext)

    def _drawPath(self):
        if self._state.path:
            self._save()
            if self._state.shadow is not None:
                self._pdfShadow(self._state.shadow)
                if self._state.gradient is not None:
                    self._save()
                    self._pdfPath(self._state.path)
                    self._state.fillColor = self._state.shadow.color
                    self._state.cmykColor = self._state.shadow.cmykColor
                    self._pdfFillColor()
                    self._state.fillColor = None
                    self._state.cmykColor = None
                    Quartz.CGContextFillPath(self._pdfContext)
                    self._restore()
            if self._state.gradient is not None:
                self._save()
                self._clipPath()
                self._pdfGradient(self._state.gradient)
                self._restore()
            elif self._state.fillColor is not None:
                self._pdfPath(self._state.path)
                self._pdfFillColor()
                Quartz.CGContextFillPath(self._pdfContext)
            if self._state.strokeColor is not None:
                self._pdfPath(self._state.path)
                self._pdfStrokeColor()
                Quartz.CGContextSetLineWidth(self._pdfContext, self._state.strokeWidth)
                if self._state.lineDash is not None:
                    Quartz.CGContextSetLineDash(self._pdfContext, 0, self._state.lineDash, len(self._state.lineDash))
                if self._state.miterLimit is not None:
                    Quartz.CGContextSetMiterLimit(self._pdfContext, self._state.miterLimit)
                if self._state.lineCap is not None:
                    Quartz.CGContextSetLineCap(self._pdfContext, self._state.lineCap)
                if self._state.lineJoin is not None:
                    Quartz.CGContextSetLineJoin(self._pdfContext, self._state.lineJoin)
                Quartz.CGContextStrokePath(self._pdfContext)
            self._restore()

    def _clipPath(self):
        if self._state.path:
            self._pdfPath(self._state.path)
            Quartz.CGContextClip(self._pdfContext)

    def _textBox(self, txt, (x, y, w, h), align):
        canDoGradients = not isinstance(txt, FormattedString)
        attrString = self.attributedString(txt, align=align)
        if self._state.text.hyphenation:
            attrString = self.hyphenateAttributedString(attrString, w)

        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = Quartz.CGPathCreateMutable()
        Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)

        ctLines = CoreText.CTFrameGetLines(box)
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        for i, (originX, originY) in enumerate(origins):
            ctLine = ctLines[i]
            bounds = CoreText.CTLineGetImageBounds(ctLine, self._pdfContext)
            if bounds.size.width == 0:
                continue
            ctRuns = CoreText.CTLineGetGlyphRuns(ctLine)
            for ctRun in ctRuns:
                attributes = CoreText.CTRunGetAttributes(ctRun)
                fillColor = attributes.get(AppKit.NSForegroundColorAttributeName)
                strokeColor = attributes.get(AppKit.NSStrokeColorAttributeName)
                strokeWidth = attributes.get(AppKit.NSStrokeWidthAttributeName, self._state.strokeWidth)

                self._save()
                drawingMode = None
                if self._state.shadow is not None:
                    self._pdfShadow(self._state.shadow)
                    if canDoGradients and self._state.gradient is not None:
                        self._save()
                        self._state.fillColor = self._state.shadow.color
                        self._state.cmykColor = self._state.shadow.cmykColor
                        self._pdfFillColor()
                        self._state.fillColor = None
                        self._state.cmykColor = None
                        Quartz.CGContextSetTextDrawingMode(self._pdfContext, Quartz.kCGTextFill)
                        Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY)
                        CoreText.CTRunDraw(ctRun, self._pdfContext, (0, 0))
                        self._restore()
                if canDoGradients and self._state.gradient is not None:
                    self._save()
                    Quartz.CGContextSetTextDrawingMode(self._pdfContext, Quartz.kCGTextClip)
                    Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY)
                    CoreText.CTRunDraw(ctRun, self._pdfContext, (0, 0))
                    self._pdfGradient(self._state.gradient)
                    self._restore()
                    drawingMode = None
                elif fillColor is not None:
                    drawingMode = Quartz.kCGTextFill
                    self._pdfFillColor(fillColor)
                if strokeColor is not None:
                    drawingMode = Quartz.kCGTextStroke
                    self._pdfStrokeColor(strokeColor)
                    Quartz.CGContextSetLineWidth(self._pdfContext, strokeWidth)
                    if self._state.lineDash is not None:
                        Quartz.CGContextSetLineDash(self._pdfContext, 0, self._state.lineDash, len(self._state.lineDash))
                    if self._state.miterLimit is not None:
                        Quartz.CGContextSetMiterLimit(self._pdfContext, self._state.miterLimit)
                    if self._state.lineCap is not None:
                        Quartz.CGContextSetLineCap(self._pdfContext, self._state.lineCap)
                    if self._state.lineJoin is not None:
                        Quartz.CGContextSetLineJoin(self._pdfContext, self._state.lineJoin)
                if fillColor is not None and strokeColor is not None:
                    drawingMode = Quartz.kCGTextFillStroke

                if drawingMode is not None:
                    Quartz.CGContextSetTextDrawingMode(self._pdfContext, drawingMode)
                    Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY)
                    CoreText.CTRunDraw(ctRun, self._pdfContext, (0, 0))
                self._restore()

    def _getImageSource(self, key):
        if isinstance(key, AppKit.NSImage):
            k = id(key)
            if k not in self._cachedImages:
                data = key.TIFFRepresentation()
                source = Quartz.CGImageSourceCreateWithData(data, {})
                self._cachedImages[k] = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
            return self._cachedImages[k]
        elif key not in self._cachedImages:
            path = key
            if path.startswith("http"):
                url = AppKit.NSURL.URLWithString_(path)
            else:
                url = AppKit.NSURL.fileURLWithPath_(path)
            source = Quartz.CGImageSourceCreateWithURL(url, None)
            if source is not None:
                self._cachedImages[key] = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
            else:
                raise DrawBotError, "No image found at %s" % key
        return self._cachedImages[key]

    def _image(self, path, (x, y), alpha):
        self._save()
        image = self._getImageSource(path)
        if image is not None:
            w = Quartz.CGImageGetWidth(image)
            h = Quartz.CGImageGetHeight(image)
            Quartz.CGContextSetAlpha(self._pdfContext, alpha)
            Quartz.CGContextDrawImage(self._pdfContext, Quartz.CGRectMake(x, y, w, h), image)
        self._restore()

    def _transform(self, transform):
        Quartz.CGContextConcatCTM(self._pdfContext, transform)

    # helpers

    def _pdfPath(self, path):
        path = path.getNSBezierPath()
        for i in range(path.elementCount()):
            instruction, points = path.elementAtIndex_associatedPoints_(i)
            if instruction == AppKit.NSMoveToBezierPathElement:
                Quartz.CGContextMoveToPoint(self._pdfContext, points[0].x, points[0].y)
            elif instruction == AppKit.NSLineToBezierPathElement:
                Quartz.CGContextAddLineToPoint(self._pdfContext, points[0].x, points[0].y)
            elif instruction == AppKit.NSCurveToBezierPathElement:
                Quartz.CGContextAddCurveToPoint(self._pdfContext, points[0].x, points[0].y, points[1].x, points[1].y, points[2].x, points[2].y)
            elif instruction == AppKit.NSClosePathBezierPathElement:
                Quartz.CGContextClosePath(self._pdfContext)

    def _pdfFillColor(self, c=None):
        if c is None:
            if self._state.cmykFillColor:
                c = self._state.cmykFillColor.getNSObject()
                cgColor = self._cmykNSColorToCGColor(c)
            else:
                c = self._state.fillColor.getNSObject()
                cgColor = self._rgbNSColorToCGColor(c)
        else:
            cgColor = self._nsColorToCGColor(c)
        Quartz.CGContextSetFillColorWithColor(self._pdfContext, cgColor)

    def _pdfStrokeColor(self, c=None):
        if c is None:
            if self._state.cmykStrokeColor:
                c = self._state.cmykStrokeColor.getNSObject()
                cgColor = self._cmykNSColorToCGColor(c)
            else:
                c = self._state.strokeColor.getNSObject()
                cgColor = self._rgbNSColorToCGColor(c)
        else:
            cgColor = self._nsColorToCGColor(c)
        Quartz.CGContextSetStrokeColorWithColor(self._pdfContext, cgColor)

    def _pdfShadow(self, shadow):
        if shadow.cmykColor:
            c = shadow.cmykColor.getNSObject()
            color = self._cmykNSColorToCGColor(c)
        else:
            c = shadow.color.getNSObject()
            color = self._rgbNSColorToCGColor(c)

        Quartz.CGContextSetShadowWithColor(self._pdfContext, self._state.shadow.offset, self._state.shadow.blur, color)

    def _pdfGradient(self, gradient):
        if gradient.cmykColors:
            colorSpace = Quartz.CGColorSpaceCreateDeviceCMYK()
            colors = []
            for color in gradient.cmykColors:
                c = color.getNSObject()
                cgColor = self._cmykNSColorToCGColor(c)
                colors.append(cgColor)
        else:
            colorSpace = Quartz.CGColorSpaceCreateDeviceRGB()
            colors = []
            for color in gradient.colors:
                c = color.getNSObject()
                cgColor = self._rgbNSColorToCGColor(c)
                colors.append(cgColor)

        cgGradient = Quartz.CGGradientCreateWithColors(
            colorSpace,
            colors,
            gradient.positions)

        if gradient.gradientType == "linear":
            Quartz.CGContextDrawLinearGradient(self._pdfContext, cgGradient, gradient.start, gradient.end, Quartz.kCGGradientDrawsBeforeStartLocation|Quartz.kCGGradientDrawsAfterEndLocation)
        elif gradient.gradientType == "radial":
            Quartz.CGContextDrawRadialGradient(self._pdfContext, cgGradient, gradient.start, gradient.startRadius, gradient.end, gradient.endRadius, Quartz.kCGGradientDrawsBeforeStartLocation|Quartz.kCGGradientDrawsAfterEndLocation)

    def _nsColorToCGColor(self, c):
        if c.numberOfComponents() == 5:
            return self._cmykNSColorToCGColor(c)
        else:
            return self._rgbNSColorToCGColor(c)

    def _cmykNSColorToCGColor(self, c):
        return Quartz.CGColorCreateGenericCMYK(c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())

    def _rgbNSColorToCGColor(self, c):
        return Quartz.CGColorCreateGenericRGB(c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())



