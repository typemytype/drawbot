import AppKit
import CoreText
import Quartz

from .tools import gifTools

from .baseContext import BaseContext, FormattedString
from ..misc import DrawBotError, isPDF, isGIF
from ..macOSVersion import macOSVersion


def sendPDFtoPrinter(pdfDocument):
    printInfo = AppKit.NSPrintInfo.sharedPrintInfo()
    op = pdfDocument.getPrintOperationForPrintInfo_autoRotate_(printInfo, True)
    printPanel = op.printPanel()
    printPanel.setOptions_(AppKit.NSPrintPanelShowsCopies | AppKit.NSPrintPanelShowsPageRange | AppKit.NSPrintPanelShowsPaperSize | AppKit.NSPrintPanelShowsOrientation | AppKit.NSPrintPanelShowsScaling | AppKit.NSPrintPanelShowsPrintSelection | AppKit.NSPrintPanelShowsPreview)
    op.runOperation()


class PDFContext(BaseContext):

    fileExtensions = ["pdf"]
    saveImageOptions = [
        ("multipage", "If False, only the last page in the document will be saved into the output PDF. This value is ignored if it is None (default)."),
    ]

    def __init__(self):
        super(PDFContext, self).__init__()
        self._hasContext = False
        self._cachedImages = {}

    def _newPage(self, width, height):
        self.size(width, height)
        mediaBox = Quartz.CGRectMake(0, 0, self.width, self.height)

        # reset the context
        self.reset()
        if self._hasContext:
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

    def _saveImage(self, path, options):
        generatedObject = None
        pool = AppKit.NSAutoreleasePool.alloc().init()
        try:
            self._closeContext()
            generatedObject = self._writeDataToFile(self._pdfData, path, options)
            self._pdfContext = None
            self._pdfData = None
        finally:
            del pool
        return generatedObject

    def _writeDataToFile(self, data, path, options):
        multipage = options.get("multipage")
        if multipage is None:
            multipage = True
        if not multipage:
            pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
            page = pdfDocument.pageAtIndex_(pdfDocument.pageCount()-1)
            data = page.dataRepresentation()
        data.writeToFile_atomically_(path, True)

    def _printImage(self, pdf=None):
        if pdf:
            sendPDFtoPrinter(pdf)
        else:
            self._closeContext()
            pdfDocument = Quartz.PDFDocument.alloc().initWithData_(self._pdfData)
            sendPDFtoPrinter(pdfDocument)
            self._pdfContext = None
            self._pdfData = None

    def _save(self):
        Quartz.CGContextSaveGState(self._pdfContext)

    def _restore(self):
        Quartz.CGContextRestoreGState(self._pdfContext)

    def _blendMode(self, operation):
        value = self._blendModeMap[operation]
        Quartz.CGContextSetBlendMode(self._pdfContext, value)

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

    def _textBox(self, txt, box, align):
        path, (x, y) = self._getPathForFrameSetter(box)

        canDoGradients = not isinstance(txt, FormattedString)
        attrString = self.attributedString(txt, align=align)
        if self._state.hyphenation:
            attrString = self.hyphenateAttributedString(attrString, path)

        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        frame = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)

        ctLines = CoreText.CTFrameGetLines(frame)
        origins = CoreText.CTFrameGetLineOrigins(frame, (0, len(ctLines)), None)
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
                baselineShift = attributes.get(AppKit.NSBaselineOffsetAttributeName, 0)
                url = attributes.get(AppKit.NSLinkAttributeName)
                self._save()
                if url is not None:
                    self._save()
                    Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY+baselineShift)
                    urlBox = CoreText.CTRunGetImageBounds(ctRun, self._pdfContext, (0, 0))
                    urlBox = Quartz.CGContextConvertRectToDeviceSpace(self._pdfContext, urlBox)
                    Quartz.CGPDFContextSetURLForRect(self._pdfContext, url, urlBox)
                    self._restore()
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
                        Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY+baselineShift)
                        CoreText.CTRunDraw(ctRun, self._pdfContext, (0, 0))
                        self._restore()
                if canDoGradients and self._state.gradient is not None:
                    self._save()
                    Quartz.CGContextSetTextDrawingMode(self._pdfContext, Quartz.kCGTextClip)
                    Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY+baselineShift)
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
                    Quartz.CGContextSetLineWidth(self._pdfContext, abs(strokeWidth))
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
                    if macOSVersion >= "10.11" and macOSVersion < "10.13":
                        # solve bug in OSX where the stroke color is the same as the fill color
                        # simple solution: draw it twice...
                        drawingMode = Quartz.kCGTextFill
                        Quartz.CGContextSetTextDrawingMode(self._pdfContext, drawingMode)
                        Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY+baselineShift)
                        CoreText.CTRunDraw(ctRun, self._pdfContext, (0, 0))
                        drawingMode = Quartz.kCGTextStroke

                if drawingMode is not None:
                    Quartz.CGContextSetTextDrawingMode(self._pdfContext, drawingMode)
                    Quartz.CGContextSetTextPosition(self._pdfContext, x+originX, y+originY+baselineShift)
                    CoreText.CTRunDraw(ctRun, self._pdfContext, (0, 0))
                self._restore()

    def _getImageSource(self, key, pageNumber):
        path = key
        image = None
        _isPDF = False
        if isinstance(key, AppKit.NSImage):
            image = key
            key = id(key)
        if pageNumber is not None:
            key = "%s-%s" % (key, pageNumber)
        if key not in self._cachedImages:
            if image is None:
                if path.startswith("http"):
                    url = AppKit.NSURL.URLWithString_(path)
                else:
                    url = AppKit.NSURL.fileURLWithPath_(path)
                _isPDF, _ = isPDF(url)
                _isGIF, _ = isGIF(url)
                if _isPDF:
                    pdf = Quartz.CGPDFDocumentCreateWithURL(url)
                    if pdf is not None:
                        if pageNumber is None:
                            pageNumber = Quartz.CGPDFDocumentGetNumberOfPages(pdf)
                        self._cachedImages[key] = _isPDF, Quartz.CGPDFDocumentGetPage(pdf, pageNumber)
                    else:
                        raise DrawBotError("No pdf found at %s" % key)
                elif _isGIF:
                    if pageNumber is None:
                        pageNumber = gifTools.gifFrameCount(url)
                    image = gifTools.gifFrameAtIndex(url, pageNumber-1)
                    data = image.TIFFRepresentation()
                    source = Quartz.CGImageSourceCreateWithData(data, {})
                    if source is not None:
                        self._cachedImages[key] = False, Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
                    else:
                        raise DrawBotError("No image found at frame %s in %s" % (pageNumber, key))
                else:
                    image = AppKit.NSImage.alloc().initByReferencingURL_(url)
            if image and not _isPDF:
                data = image.TIFFRepresentation()
                source = Quartz.CGImageSourceCreateWithData(data, {})
                if source is not None:
                    self._cachedImages[key] = _isPDF, Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
                else:
                    raise DrawBotError("No image found at %s" % key)
        return self._cachedImages[key]

    def _image(self, path, xy, alpha, pageNumber):
        x, y = xy
        self._save()
        _isPDF, image = self._getImageSource(path, pageNumber)
        if image is not None:
            Quartz.CGContextSetAlpha(self._pdfContext, alpha)
            if _isPDF:
                Quartz.CGContextSaveGState(self._pdfContext)
                Quartz.CGContextTranslateCTM(self._pdfContext, x, y)
                Quartz.CGContextDrawPDFPage(self._pdfContext, image)
                Quartz.CGContextRestoreGState(self._pdfContext)
            else:
                w = Quartz.CGImageGetWidth(image)
                h = Quartz.CGImageGetHeight(image)
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
        # XXX
        # needs to be solved
        # for now adjust the documentation
        # currentTransformation = Quartz.CGContextGetUserSpaceToDeviceSpaceTransform(self._pdfContext)
        # scaleX = math.sqrt(currentTransformation[0] * currentTransformation[0] + currentTransformation[1] * currentTransformation[1])
        # scaleY = math.sqrt(currentTransformation[2] * currentTransformation[2] + currentTransformation[3] * currentTransformation[3])
        x, y = self._state.shadow.offset
        # x *= scaleX
        # y *= scaleY
        blur = self._state.shadow.blur
        # blur *= (scaleX + scaleY) / 2.
        Quartz.CGContextSetShadowWithColor(self._pdfContext, (x, y), blur, color)

    def _pdfGradient(self, gradient):
        if gradient.cmykColors:
            colorSpace = Quartz.CGColorSpaceCreateDeviceCMYK()
            colors = []
            for color in gradient.cmykColors:
                c = color.getNSObject()
                cgColor = self._cmykNSColorToCGColor(c)
                colors.append(cgColor)
        else:
            colorSpace = self._colorClass.colorSpace.CGColorSpace()
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
            Quartz.CGContextDrawLinearGradient(self._pdfContext, cgGradient, gradient.start, gradient.end, Quartz.kCGGradientDrawsBeforeStartLocation | Quartz.kCGGradientDrawsAfterEndLocation)
        elif gradient.gradientType == "radial":
            Quartz.CGContextDrawRadialGradient(self._pdfContext, cgGradient, gradient.start, gradient.startRadius, gradient.end, gradient.endRadius, Quartz.kCGGradientDrawsBeforeStartLocation | Quartz.kCGGradientDrawsAfterEndLocation)

    def _nsColorToCGColor(self, c):
        if c.numberOfComponents() == 5:
            return self._cmykNSColorToCGColor(c)
        else:
            return self._rgbNSColorToCGColor(c)

    def _cmykNSColorToCGColor(self, c):
        return Quartz.CGColorCreateGenericCMYK(c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())

    def _rgbNSColorToCGColor(self, c):
        if c.numberOfComponents() == 2:
            # gray color
            return Quartz.CGColorCreateGenericGray(c.whiteComponent(), c.alphaComponent())
        return Quartz.CGColorCreateGenericRGB(c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())

    def _linkURL(self, url, xywh):
        url = AppKit.NSURL.URLWithString_(url)
        x, y, w, h = xywh
        rectBox = Quartz.CGRectMake(x, y, w, h)
        Quartz.CGPDFContextSetURLForRect(self._pdfContext, url, rectBox)

    def _linkDestination(self, name, xy):
        x, y = xy
        if (x, y) == (None, None):
            x, y = self.width * 0.5, self.height * 0.5
        x = max(0, min(x, self.width))
        y = max(0, min(y, self.height))
        centerPoint = Quartz.CGPoint(x, y)
        Quartz.CGPDFContextAddDestinationAtPoint(self._pdfContext, name, centerPoint)

    def _linkRect(self, name, xywh):
        x, y, w, h = xywh
        rectBox = Quartz.CGRectMake(x, y, w, h)
        Quartz.CGPDFContextSetDestinationForRect(self._pdfContext, name, rectBox)
