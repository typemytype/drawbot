import AppKit
import Quartz
from distutils.version import StrictVersion
import platform

osVersionCurrent = StrictVersion(platform.mac_ver()[0])
if osVersionCurrent >= StrictVersion("10.15"):
    # QTKit is being deprecated
    QTKit = None
else:
    import QTKit

import os

from drawBot.misc import DrawBotError, warnings
from drawBot.scriptTools import osVersionCurrent
from .pdfContext import PDFContext


class MOVContext(PDFContext):

    fileExtensions = ["mov"]
    saveImageOptions = []

    if QTKit is not None:
        _saveMovieAttributes = {
            QTKit.QTAddImageCodecType: "png "
        }

    _frameLength = 3000
    _frameScale = 30000

    def __init__(self):
        super(MOVContext, self).__init__()
        if QTKit is None:
            raise DrawBotError("Export to '.mov' was deprecated and is not supported on this system (10.15 and up). Use .mp4 instead.")
        self._frameDurationData = []

    def _newPage(self, width, height):
        super(MOVContext, self)._newPage(width, height)
        self._frameDurationData.append((self._frameLength, self._frameScale))
        self.save()
        self.fill(1, 1, 1, 1)
        self.rect(0, 0, self.width, self.height)
        self.restore()

    def _frameDuration(self, seconds):
        length = seconds * self._frameScale
        self._frameDurationData[-1] = length, self._frameScale

    def _writeDataToFile(self, data, path, options):
        if os.path.exists(path):
            os.remove(path)
        warnings.warn("Export to '.mov' is deprecated, use '.mp4' instead.")
        movie, error = QTKit.QTMovie.alloc().initToWritableFile_error_(path, None)
        if error:
            raise DrawBotError("Could not create a quick time movie, %s" % error.localizedDescription())

        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)

        for index in range(pdfDocument.pageCount()):
            pool = AppKit.NSAutoreleasePool.alloc().init()
            try:
                frameLength, frameScale = self._frameDurationData[index]
                duration = QTKit.QTMakeTime(frameLength, frameScale)
                page = pdfDocument.pageAtIndex_(index)
                image = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
                movie.addImage_forDuration_withAttributes_(image, duration, self._saveMovieAttributes)
            finally:
                del pool
        movie.updateMovieFile()
