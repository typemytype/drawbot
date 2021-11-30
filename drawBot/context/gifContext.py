import Quartz
import os
import glob
import tempfile

from .imageContext import ImageContext, getSaveImageOptions

from .tools.gifTools import generateGif


class GIFContext(ImageContext):

    fileExtensions = ["gif"]

    saveImageOptions = getSaveImageOptions([
        "imageGIFDitherTransparency",
        "imageGIFRGBColorTable",
        "imageColorSyncProfileData",
    ]) + [
        ("imageGIFLoop", "Boolean that indicates whether the animated gif should loop")
    ]

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
            tempDir = tempfile.mkdtemp(suffix=".giftmp")
            tempPath = os.path.join(tempDir, "frame.gif")

        super(GIFContext, self)._writeDataToFile(data, tempPath, options)

        if shouldBeAnimated:
            def getFrameNumber(name):
                fileName = os.path.basename(name)
                num = fileName[6:-4]
                return int(num)

            inputPaths = sorted(glob.glob(tempDir + "frame_*.gif"), key=getFrameNumber)

            generateGif(inputPaths, path, self._delayData, options.get("imageGIFLoop", True))
