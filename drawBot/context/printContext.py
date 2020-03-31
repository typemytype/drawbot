import AppKit
from fontTools.pens.basePen import AbstractPen

from .baseContext import BaseContext


class StringPen(AbstractPen):

    def __init__(self, seperator=None):
        self.data = []
        if seperator is None:
            seperator = " "
        self.seperator = seperator

    def moveTo(self, pt):
        x, y = pt
        self.data.append("moveTo %s %s" % (x, y))

    def lineTo(self, pt):
        x, y = pt
        self.data.append("lineTo %s %s" % (x, y))

    def curveTo(self, *pts):
        self.data.append("curveTo %s" % " ".join(["%s %s" % (x, y) for x, y in pts]))

    def qCurveTo(self, *pts):
        self.data.append("qCurveTo %s" % " ".join(["%s %s" % (x, y) for x, y in pts]))

    def closePath(self):
        self.data.append("closePath")

    def endPath(self):
        self.data.append("endPath")

    def __repr__(self):
        return self.seperator.join(self.data)


class PrintContext(BaseContext):

    fileExtensions = ["*"]
    validateSaveImageOptions = False

    def _newPage(self, width, height):
        print("newPage %s %s" % (width, height))

    def _save(self):
        print("save")

    def _restore(self):
        print("restore")

    def _blendMode(self, operation):
        print("blendMode %s" % operation)

    def _drawPath(self):
        pen = StringPen()
        self._state.path.drawToPen(pen)
        print("drawPath %s" % pen)

    def _clipPath(self):
        pen = StringPen()
        self._state.path.drawToPen(pen)
        print("clipPath %s" % pen)

    def _transform(self, matrix):
        print("transform %s" % " ".join(["%s" % i for i in matrix]))

    def _textBox(self, txt, xywh, align):
        # XXX
        # should a formatted string be printed in parts???
        x, y, w, h = xywh
        print("textBox %s %r %r %r %r %s" % (txt, x, y, w, h, align))

    def _image(self, path, xy, alpha, pageNumber):
        x, y = xy
        if isinstance(path, AppKit.NSImage):
            path = "Image Object"
        print("image %s %s %s %s %s" % (path, x, y, alpha, pageNumber))

    def _frameDuration(self, seconds):
        print("frameDuration %s" % seconds)

    def _reset(self, other=None):
        print("reset %s" % other)

    def _saveImage(self, path, options):
        print("saveImage %s %s" % (path, options))

    def _printImage(self, pdf=None):
        print("printImage %s" % pdf)

    def _linkURL(self, url, xywh):
        x, y, w, h = xywh
        print("linkURL %s %s %s %s %s" % (url, x, y, w, h))

    def _linkDestination(self, name, xy):
        x, y = xy
        print("linkDestination %s %s %s" % (name, x, y))

    def _linkRect(self, name, xywh):
        x, y, w, h = xywh
        print("linkRect %s %s %s %s %s" % (name, x, y, w, h))
