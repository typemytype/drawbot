## read the docs hack
try:
    from Quartz import *
    from QTKit import *
except:
    pass

import os

from drawBot.misc import DrawBotError
from pdfContext import PDFContext

class MOVContext(PDFContext):
    
    fileExtensions = ["mov"]

    _saveMovieAttributes = {
        QTAddImageCodecType : "png "
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
        length = seconds * self._frameScale
        self._frameDurationData[-1] = length, self._frameScale

    def _writeDataToFile(self, data, path):
        if os.path.exists(path):
            os.remove(path)
        movie, error = QTMovie.alloc().initToWritableFile_error_(path, None)
        if error:
            raise DrawBotError, "Could not create a quick time movie, %s" % error.localizedDescription()
        
        pdfDocument = PDFDocument.alloc().initWithData_(data)

        for index in range(pdfDocument.pageCount()):
            frameLength, frameScale = self._frameDurationData[index]
            duration = QTMakeTime(frameLength, frameScale)
            page = pdfDocument.pageAtIndex_(index)
            image = NSImage.alloc().initWithData_(page.dataRepresentation())
            movie.addImage_forDuration_withAttributes_(image, duration, self._saveMovieAttributes)
        movie.updateMovieFile()