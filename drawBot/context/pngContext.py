import tempfile

import Quartz  # type: ignore

from .imageContext import ImageContext, getSaveImageOptions
from .tools.apng import APNG


class PNGContext(ImageContext):
    fileExtensions = ["png"]

    saveImageOptions = getSaveImageOptions(
        [
            "imagePNGGamma",
            "imagePNGInterlaced",
            "imageColorSyncProfileData",
        ]
    )

    _delay_den = 100
    _delay = 1 / _delay_den

    def __init__(self):
        super().__init__()
        self._delayData = []

    def _frameDuration(self, seconds):
        # `delay_num` specifies 1/100ths of a second; see https://wiki.mozilla.org/APNG_Specification#.60fcTL.60:_The_Frame_Control_Chunk%3E
        self._delayData[-1] = int(seconds * self._delay_den)

    def _newPage(self, width, height):
        super()._newPage(width, height)
        self._delayData.append(self._delay)

    def _writeDataToFile(self, data, path, options):
        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
        pageCount = pdfDocument.pageCount()
        shouldBeAnimated = pageCount > 1

        tempPath = path
        if shouldBeAnimated:
            options["multipage"] = True
            tempPath = tempfile.mkstemp(suffix=".png")[1]

        self._inputPaths = []
        super()._writeDataToFile(data, tempPath, options)

        if shouldBeAnimated:
            animatedPNG = APNG()
            for inputPath, delay in zip(self._inputPaths, self._delayData):
                animatedPNG.append_file(inputPath, delay=delay, delay_den=self._delay_den)
            animatedPNG.save(path)
        del self._inputPaths

    def _storeImageData(self, imageData, imagePath):
        super()._storeImageData(imageData, imagePath)
        self._inputPaths.append(imagePath)
