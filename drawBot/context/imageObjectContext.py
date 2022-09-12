import io
import AppKit
try:
    from PIL import Image
    hasPIL = True
except ImportError:
    hasPIL = False

from .imageContext import ImageContext
from drawBot.misc import DrawBotError


class BaseImageObjectContext(ImageContext):

    def _writeDataToFile(self, data, path, options):
        self._imageObjects = []
        # we just need a path with a file extension
        # nothing will be written to disk
        super()._writeDataToFile(data, "temp.tiff", options)
        imageObjects = self._imageObjects
        del self._imageObjects
        if not options.get("multipage"):
            imageObjects = imageObjects[0]
        return imageObjects

    def _storeImageData(self, imageData, imagePath):
        obj = self._getObjectForData(imageData)
        self._imageObjects.append(obj)

    def _getObjectForData(self, data):
        raise NotImplementedError


class PILContext(BaseImageObjectContext):

    fileExtensions = ["PIL"]

    def __init__(self):
        if not hasPIL:
            raise DrawBotError("The package PIL is required.")
        super().__init__()

    def _getObjectForData(self, data):
        file = io.BytesIO(data.bytes())
        return Image.open(file)


class NSImageContext(BaseImageObjectContext):

    fileExtensions = ["NSImage"]

    def _getObjectForData(self, data):
        return AppKit.NSImage.alloc().initWithData_(data)
