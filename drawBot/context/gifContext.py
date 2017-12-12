from __future__ import absolute_import

import AppKit
import Quartz

import tempfile

from .imageContext import ImageContext

from .tools.gifTools import generateGif


class GifContext(ImageContext):

    _saveImageFileTypes = {
        "gif": AppKit.NSGIFFileType,
    }

    fileExtensions = _saveImageFileTypes.keys()

    _delay = 10

    def __init__(self):
        super(GifContext, self).__init__()
        self._delayData = []

    def _frameDuration(self, seconds):
        # gifsicle -h: Set frame delay to TIME (in 1/100sec).
        self._delayData[-1] = int(seconds * 100)

    def _newPage(self, width, height):
        super(GifContext, self)._newPage(width, height)
        self._delayData.append(self._delay)

    def _writeDataToFile(self, data, path, multipage, options):
        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
        pageCount = pdfDocument.pageCount()
        shouldBeAnimated = pageCount > 1

        tempPath = path
        if shouldBeAnimated:
            tempPath = tempfile.mkstemp(suffix=".gif")[1]

        inputPaths = super(GifContext, self)._writeDataToFile(data, tempPath, shouldBeAnimated, options)

        if shouldBeAnimated:
            generateGif(inputPaths, path, self._delayData)
