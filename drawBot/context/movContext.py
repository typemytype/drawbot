from __future__ import absolute_import

import AppKit
import QTKit
import Quartz

import os

from drawBot.misc import DrawBotError
from .pdfContext import PDFContext


class MOVContext(PDFContext):

    fileExtensions = ["mov"]
    saveImageOptions = []

    _saveMovieAttributes = {
        QTKit.QTAddImageCodecType: "png "
    }

    _frameLength = 3000
    _frameScale = 30000

    def __init__(self):
        super(MOVContext, self).__init__()
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
