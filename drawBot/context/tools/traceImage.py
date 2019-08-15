import AppKit
import tempfile
from xml.dom import minidom
import os

from fontTools.misc.transform import Transform

from .imageObject import ImageObject
from drawBot.misc import executeExternalProcess, getExternalToolPath


def _getPath(element, path=None, pathItems=None):
    if pathItems is None:
        pathItems = list()

    children = [child for child in element.childNodes if child.nodeType == 1]
    for child in children:
        if child.tagName == "g":
            # group
            path = dict(coordinates=[])
            pathItems.append(path)
            for name, value in child.attributes.items():
                if name == "transform":
                    t = Transform()
                    for trans in value.split(" "):
                        key, v = trans.split("(")
                        if key.lower() != "scale":
                            continue
                        if ")" in v:
                            v = v.replace(")", "")
                        x, y = v.split(",")
                        x = float(x)
                        y = float(y)
                        y = x
                        t = getattr(t, key)(x, y)
                    path["transform"] = t
            _getPath(child, path, pathItems)
        elif child.tagName == "path":
            # path
            if path is None:
                path = dict(coordinates=[])
                pathItems.append(path)
            for name, value in child.attributes.items():
                path["coordinates"].append(value.split(" "))
        else:
            continue
    return pathItems


class BaseSegment(object):

    def __init__(self):
        self._points = []

    def addPoint(self, p):
        self._points.append(p)

    def bezier(self, pen):
        pass


class AbsMoveTo(BaseSegment):

    def bezier(self, pen):
        for p in self._points:
            pen._moveTo(p)


class RelMoveTo(BaseSegment):

    def bezier(self, pen):
        for p in self._points:
            pen._relMoveTo(p)


class AbsLineTo(BaseSegment):

    def bezier(self, pen):
        for p in self._points:
            pen._lineTo(p)


class RelLineTo(BaseSegment):

    def bezier(self, pen):
        for p in self._points:
            pen._relLineTo(p)


class AbsCurveTo(BaseSegment):

    def bezier(self, pen):
        for i in range(2, len(self._points), 3):
            h1 = self._points[i - 2]
            h2 = self._points[i - 1]
            p = self._points[i]
            pen._curveTo(h1, h2, p)


class RelCurveTo(BaseSegment):

    def bezier(self, pen):
        for i in range(2, len(self._points), 3):
            h1 = self._points[i - 2]
            h2 = self._points[i - 1]
            p = self._points[i]
            pen._relCurveTo(h1, h2, p)


class RelClosePath(BaseSegment):

    def bezier(self, pen):
        pen._closePath()


class AbsClosePath(BaseSegment):

    def bezier(self, pen):
        pen._closePath()


class RelativePen:

    def __init__(self, outPen, transform):
        self.outPen = outPen
        self.transform = transform
        self.currentPoint = (0, 0)

    def _moveTo(self, p):
        self.currentPoint = p
        if self.transform:
            p = self.transform.transformPoint(p)
        self.outPen.moveTo(p)

    def _relMoveTo(self, p):
        x, y = p
        cx, cy = self.currentPoint
        self._moveTo((cx + x, cy + y))

    def _lineTo(self, p):
        self.currentPoint = p
        if self.transform:
            p = self.transform.transformPoint(p)
        self.outPen.lineTo(p)

    def _relLineTo(self, p):
        x, y = p
        cx, cy = self.currentPoint
        self._lineTo((cx + x, cy + y))

    def _curveTo(self, h1, h2, p):
        self.currentPoint = p
        if self.transform:
            h1 = self.transform.transformPoint(h1)
            h2 = self.transform.transformPoint(h2)
            p = self.transform.transformPoint(p)
        self.outPen.curveTo(h1, h2, p)

    def _relCurveTo(self, h1, h2, p):
        x1, y1 = h1
        x2, y2 = h2
        x, y = p
        cx, cy = self.currentPoint
        self._curveTo((cx + x1, cy + y1), (cx + x2, cy + y2), (cx + x, cy + y))

    def _closePath(self):
        self.outPen.closePath()


instructions = dict(
    m=RelMoveTo,
    M=AbsMoveTo,
    l=RelLineTo,
    L=AbsLineTo,
    c=RelCurveTo,
    C=AbsCurveTo,
    z=RelClosePath,
    Z=AbsClosePath
)


class Paths:

    def __init__(self):
        self._currentInstruction = None
        self._segments = list()

    def setInstruction(self, instruction):
        if instruction is None:
            return
        instruction = instructions[instruction]

        self._currentInstruction = instruction()
        self._segments.append(self._currentInstruction)

    def addPoint(self, x, y):
        self._currentInstruction.addPoint((x, y))

    def beziers(self, outPen, transfrom=None):
        pen = RelativePen(outPen, transfrom)
        for seg in self._segments:
            seg.bezier(pen)


def importSVGWithPen(svgPath, outPen, box=None, offset=None):
    svgDoc = minidom.parse(svgPath)
    svgParent = svgDoc.documentElement

    scaleX = scaleY = 1
    if offset is None:
        offset = 0, 0
    offsetX, offsetY = offset
    translate = (offsetX, offsetY)
    if box is not None:
        (x, y, w, h) = box
        translate = (x + offsetX, y + offsetY)

        docWidth = float(svgParent.attributes["width"].value[:-2])
        docHeight = float(svgParent.attributes["height"].value[:-2])

        scaleX = w / docWidth
        scaleY = h / docHeight

    svgPaths = _getPath(svgParent)
    for path in svgPaths:
        paths = Paths()
        transform = path.get("transform").reverseTransform(Transform().translate(*translate).scale(scaleX, scaleY))

        allCoordinates = path.get("coordinates")
        for coordinates in allCoordinates:
            for i in range(1, len(coordinates), 2):
                x = coordinates[i - 1]
                y = coordinates[i]

                instruction = None
                closePath = False
                if x[0] in instructions:
                    instruction = x[0]
                    x = x[1:]
                if y[-1] in instructions:
                    closePath = True
                    y = y[:-1]
                x = float(x)
                y = float(y)

                paths.setInstruction(instruction)
                paths.addPoint(x, y)

                if closePath:
                    closePath = False
                    paths.setInstruction("z")

        paths.beziers(outPen, transform)


def saveImageAsBitmap(image, bitmapPath):
    # http://stackoverflow.com/questions/23258596/how-to-save-png-file-from-nsimage-retina-issues-the-right-way
    x, y = image.offset()
    width, height = image.size()

    bitmap = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bitmapFormat_bytesPerRow_bitsPerPixel_(
        None,  # data planes
        int(width),  # pixels wide
        int(height),  # pixels high
        8,  # bits per sample
        4,  # samples per pixel
        True,  # has alpha
        False,  # is planar
        AppKit.NSDeviceRGBColorSpace,  # color space
        0,  # bitmap format
        0,  # bytes per row
        0   # bits per pixel
    )

    AppKit.NSGraphicsContext.saveGraphicsState()
    AppKit.NSGraphicsContext.setCurrentContext_(AppKit.NSGraphicsContext.graphicsContextWithBitmapImageRep_(bitmap))
    AppKit.NSGraphicsContext.currentContext().setShouldAntialias_(True)

    AppKit.NSColor.whiteColor().set()
    AppKit.NSRectFill(((0, 0), (width, height)))

    image._ciImage().drawAtPoint_fromRect_operation_fraction_((x, y), AppKit.NSMakeRect(0, 0, width, height), AppKit.NSCompositeSourceOver, 1)

    AppKit.NSGraphicsContext.restoreGraphicsState()

    data = bitmap.representationUsingType_properties_(AppKit.NSBMPFileType, {AppKit.NSImageCompressionFactor: 1})
    data.writeToFile_atomically_(bitmapPath, True)


def TraceImage(path, outPen, threshold=.2, blur=None, invert=False, turd=2, tolerance=0.2, offset=None):
    potrace = getExternalToolPath(os.path.dirname(__file__), "potrace")
    mkbitmap = getExternalToolPath(os.path.dirname(__file__), "mkbitmap")

    if isinstance(path, ImageObject):
        image = path
    else:
        image = ImageObject(path)

    x, y = image.offset()
    w, h = image.size()

    imagePath = tempfile.mktemp(".bmp")
    bitmapPath = tempfile.mktemp(".pgm")
    svgPath = tempfile.mktemp(".svg")

    saveImageAsBitmap(image, imagePath)

    assert mkbitmap is not None
    cmds = [mkbitmap, "-x", "-t", str(threshold)]
    if blur:
        cmds.extend(["-b", str(blur)])
    if invert:
        cmds.extend(["-i"])
    cmds.extend([
        # "-g",
        # "-1",
        "-o",
        bitmapPath,
        imagePath
    ])
    log = executeExternalProcess(cmds)
    if log != ('', ''):
        print(log)

    assert potrace is not None
    cmds = [potrace, "-s"]
    cmds.extend(["-t", str(turd)])
    cmds.extend(["-O", str(tolerance)])
    cmds.extend(["-o", svgPath, bitmapPath])

    log = executeExternalProcess(cmds)
    if log != ('', ''):
        print(log)

    importSVGWithPen(svgPath, outPen, (x, y, w, h), offset)

    os.remove(imagePath)
    os.remove(svgPath)
    os.remove(bitmapPath)
