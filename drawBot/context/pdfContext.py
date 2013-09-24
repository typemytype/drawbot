from AppKit import *
from CoreText import *
from Quartz import *

from baseContext import BaseContext

class PDFContext(BaseContext):
    
    fileExtensions = ["pdf"]

    def __init__(self):
        super(PDFContext, self).__init__()
        self._hasContext = False        

    def _newPage(self, width, height):
        self.size(width, height)
        mediaBox = CGRectMake(0, 0, self.width, self.height)
        pageInfo = { kCGPDFContextMediaBox : mediaBox}

        if self._hasContext:
            # reset the context
            self.reset()
            # add a new page
            CGPDFContextEndPage(self._pdfContext)
            CGPDFContextBeginPage(self._pdfContext, pageInfo)
        else:
            # create a new pdf document
            self._pdfData = CFDataCreateMutable(None, 0)
            dataConsumer = CGDataConsumerCreateWithCFData(self._pdfData)
            self._pdfContext = CGPDFContextCreate(dataConsumer, mediaBox, None)
            CGPDFContextBeginPage(self._pdfContext, pageInfo)
            self._hasContext = True

    def _closeContext(self):
        CGPDFContextEndPage(self._pdfContext)
        CGPDFContextClose(self._pdfContext)
        self._hasContext = False

    def _saveImage(self, path):
        self._closeContext()
        self._writeDataToFile(self._pdfData, path)
        self._pdfContext = None
        self._pdfData = None

    def _writeDataToFile(self, data, path):
        data.writeToFile_atomically_(path, True)

    def _save(self):
        CGContextSaveGState(self._pdfContext)

    def _restore(self):
        CGContextRestoreGState(self._pdfContext)

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
                    CGContextEOFillPath(self._pdfContext)
                    self._restore()
            if self._state.gradient is not None:
                self._save()
                self._clipPath()
                self._pdfGradient(self._state.gradient)
                self._restore()
            elif self._state.fillColor is not None:
                self._pdfPath(self._state.path)
                self._pdfFillColor()
                CGContextEOFillPath(self._pdfContext)
            if self._state.strokeColor is not None:
                self._pdfPath(self._state.path)
                self._pdfStrokeColor()
                CGContextSetLineWidth(self._pdfContext, self._state.strokeWidth)
                if self._state.lineDash is not None:
                    CGContextSetLineDash(self._pdfContext, 0, self._state.lineDash, len(self._state.lineDash))
                if self._state.miterLimit is not None:
                    CGContextSetMiterLimit(self._pdfContext, self._state.miterLimit)
                if self._state.lineCap is not None:
                    CGContextSetLineCap(self._pdfContext, self._state.lineCap)
                if self._state.lineJoin is not None:
                    CGContextSetLineJoin(self._pdfContext, self._state.lineJoin)
                CGContextStrokePath(self._pdfContext)
            self._restore()

    def _clipPath(self):
        if self._state.path:
            self._pdfPath(self._state.path)
            CGContextEOClip(self._pdfContext)

    def _textBox(self, txt, (x, y, w, h), align):
        attrString = self.attributedString(txt, align=align)
        setter = CTFramesetterCreateWithAttributedString(attrString)
        path = CGPathCreateMutable()
        CGPathAddRect(path, None, CGRectMake(x, y, w, h))
        box = CTFramesetterCreateFrame(setter, (0, 0), path, None)

        lines = []
            
        ctLines = CTFrameGetLines(box)
        for ctLine in ctLines:
            r = CTLineGetStringRange(ctLine)
            line = txt[r.location:r.location+r.length]
            while line and line[-1] == " ":
                line = line[:-1]
            lines.append(line.replace("\n", ""))

        origins = CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        for i, (originX, originY) in enumerate(origins):
            line = lines[i]

            self._save()
            CGContextSelectFont(self._pdfContext, self._state.text.fontName, self._state.text.fontSize, kCGEncodingMacRoman)
            drawingMode = None
            if self._state.shadow is not None:
                self._pdfShadow(self._state.shadow)
                if self._state.gradient is not None:
                    self._save()
                    self._state.fillColor = self._state.shadow.color
                    self._state.cmykColor = self._state.shadow.cmykColor
                    self._pdfFillColor()
                    self._state.fillColor = None
                    self._state.cmykColor = None
                    CGContextSetTextDrawingMode(self._pdfContext, kCGTextFill)
                    CGContextShowTextAtPoint(self._pdfContext, x+originX, y+originY, line, len(line))
                    self._restore()
            if self._state.gradient is not None:
                self._save()
                CGContextSetTextDrawingMode(self._pdfContext, kCGTextClip)
                CGContextShowTextAtPoint(self._pdfContext, x+originX, y+originY, line, len(line))
                self._pdfGradient(self._state.gradient)
                self._restore()
                drawingMode = None
            elif self._state.fillColor is not None:
                drawingMode = kCGTextFill
                self._pdfFillColor()
            if self._state.strokeColor is not None:
                drawingMode = kCGTextStroke
                self._pdfStrokeColor()
                strokeWidth = self._state.strokeWidth
                CGContextSetLineWidth(self._pdfContext, self._state.strokeWidth)
                if self._state.lineDash is not None:
                    CGContextSetLineDash(self._pdfContext, 0, self._state.lineDash, len(self._state.lineDash))
                if self._state.miterLimit is not None:
                    CGContextSetMiterLimit(self._pdfContext, self._state.miterLimit)
                if self._state.lineCap is not None:
                    CGContextSetLineCap(self._pdfContext, self._state.lineCap)
                if self._state.lineJoin is not None:
                    CGContextSetLineJoin(self._pdfContext, self._state.lineJoin)
            if self._state.fillColor is not None and self._state.strokeColor is not None:
                drawingMode = kCGTextFillStroke
            
            if drawingMode is not None:
                CGContextSetTextDrawingMode(self._pdfContext, drawingMode)
                CGContextShowTextAtPoint(self._pdfContext, x+originX, y+originY, line, len(line))
            self._restore()

    def _image(self, path, (x, y), alpha):
        self._save()
        if path.startswith("http"):
            url = NSURL.URLWithString_(path)
        else:
            url = NSURL.fileURLWithPath_(path)
        source = CGImageSourceCreateWithURL(url, None)
        if source is not None:
            image = CGImageSourceCreateImageAtIndex(source, 0, None)
            w = CGImageGetWidth(image)
            h = CGImageGetHeight(image)
            CGContextSetAlpha(self._pdfContext, alpha)
            CGContextDrawImage(self._pdfContext, CGRectMake(x, y, w, h), image)
        self._restore()

    def _transform(self, transform):
        CGContextConcatCTM(self._pdfContext, transform)

    # helpers

    def _pdfPath(self, path):
        path = path.getNSBezierPath()
        for i in range(path.elementCount()):
            instruction, points = path.elementAtIndex_associatedPoints_(i)
            if instruction == NSMoveToBezierPathElement:
                CGContextMoveToPoint(self._pdfContext, points[0].x, points[0].y)
            elif instruction == NSLineToBezierPathElement:
                CGContextAddLineToPoint(self._pdfContext, points[0].x, points[0].y)
            elif instruction == NSCurveToBezierPathElement:
                CGContextAddCurveToPoint(self._pdfContext, points[0].x, points[0].y, points[1].x, points[1].y, points[2].x, points[2].y)
            elif instruction == NSClosePathBezierPathElement:
                CGContextClosePath(self._pdfContext)

    def _pdfFillColor(self):
        if self._state.cmykFillColor:
            c = self._state.cmykFillColor.getNSObject()
            CGContextSetCMYKFillColor(self._pdfContext, c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
        else:
            c = self._state.fillColor.getNSObject()
            CGContextSetRGBFillColor(self._pdfContext, c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())
    
    def _pdfStrokeColor(self):
        if self._state.cmykStrokeColor:
            c = self._state.cmykStrokeColor.getNSObject()
            CGContextSetCMYKStrokeColor(self._pdfContext, c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
        else:
            c = self._state.strokeColor.getNSObject()
            CGContextSetRGBStrokeColor(self._pdfContext, c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())

    def _pdfShadow(self, shadow):
        if shadow.cmykColor:
            c = shadow.cmykColor.getNSObject()
            color = CGColorCreateGenericCMYK(c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
        else:
            c = shadow.color.getNSObject()
            color = CGColorCreateGenericRGB(c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())

        CGContextSetShadowWithColor(self._pdfContext, self._state.shadow.offset, self._state.shadow.blur, color)
    
    def _pdfGradient(self, gradient):
        if gradient.cmykColors:
            colorSpace = CGColorSpaceCreateDeviceCMYK()
            colors = []
            for color in gradient.cmykColors:
                c = color.getNSObject()
                cgColor = CGColorCreateGenericCMYK(c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
                colors.append(cgColor)
        else:
            colorSpace = CGColorSpaceCreateDeviceRGB()
            colors = []
            for color in gradient.colors:
                c = color.getNSObject()
                cgColor = CGColorCreateGenericRGB(c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())
                colors.append(cgColor)

        cgGradient = CGGradientCreateWithColors(
            colorSpace,
            colors,
            gradient.positions)

        if gradient.gradientType == "linear":
            CGContextDrawLinearGradient(self._pdfContext, cgGradient, gradient.start, gradient.end, kCGGradientDrawsBeforeStartLocation|kCGGradientDrawsAfterEndLocation)
        elif gradient.gradientType == "radial":
            CGContextDrawRadialGradient(self._pdfContext, cgGradient, gradient.start, gradient.startRadius, gradient.end, gradient.endRadius, kCGGradientDrawsBeforeStartLocation|kCGGradientDrawsAfterEndLocation)




