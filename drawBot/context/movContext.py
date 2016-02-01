import AppKit
import QTKit
import Quartz

import os

from drawBot.misc import DrawBotError
from pdfContext import PDFContext


class MOVContext(PDFContext):

    fileExtensions = ["mov"]

    _saveMovieAttributes = {
        QTKit.QTAddImageCodecType: "png "
        }

    _frameLength = 100
    _frameScale = 1000

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
        if type(seconds) is tuple:
            # Duration as a ratio
            self._frameDurationData[-1] = seconds
        else:
            # Duration as a fraction of a second, turn it into a ratio of _frameScale
            length = seconds * self._frameScale
            self._frameDurationData[-1] = length, self._frameScale

    def _writeDataToFile(self, data, path, multipage):
        if os.path.exists(path):
            os.remove(path)
        movie, error = QTKit.QTMovie.alloc().initToWritableFile_error_(path, None)
        if error:
            raise DrawBotError("Could not create a quick time movie, %s" % error.localizedDescription())

        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)

        for index in range(pdfDocument.pageCount()):
            pool = AppKit.NSAutoreleasePool.alloc().init()
            frameLength, frameScale = self._frameDurationData[index]
            duration = QTKit.QTMakeTime(frameLength, frameScale)
            page = pdfDocument.pageAtIndex_(index)
            image = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
            movie.addImage_forDuration_withAttributes_(image, duration, self._saveMovieAttributes)
            del pool
        movie.updateMovieFile()
