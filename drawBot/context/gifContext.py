import Quartz

import tempfile

from .imageContext import ImageContext, getSaveImageOptions

from .tools.gifTools import generateGif


class GIFContext(ImageContext):

    fileExtensions = ["gif"]

    saveImageOptions = getSaveImageOptions([
        "imageGIFDitherTransparency",
        "imageGIFRGBColorTable",
        "imageColorSyncProfileData",
    ])

    _delay = 10

    def __init__(self):
        super(GIFContext, self).__init__()
        self._delayData = []

    def _frameDuration(self, seconds):
        # gifsicle -h: Set frame delay to TIME (in 1/100sec).
        self._delayData[-1] = int(seconds * 100)

    def _newPage(self, width, height):
        super(GIFContext, self)._newPage(width, height)
        self._delayData.append(self._delay)

    def _writeDataToFile(self, data, path, options):
        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
        pageCount = pdfDocument.pageCount()
        shouldBeAnimated = pageCount > 1

        tempPath = path
        if shouldBeAnimated:
            options["multipage"] = True
            tempPath = tempfile.mkstemp(suffix=".gif")[1]

        inputPaths = super(GIFContext, self)._writeDataToFile(data, tempPath, options)

        if shouldBeAnimated:
            generateGif(inputPaths, path, self._delayData)
