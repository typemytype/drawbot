import tempfile

from PIL import Image
import io
import AppKit

from .imageContext import ImageContext

class BaseImageObjectContext(ImageContext):

    def _writeDataToFile(self, data, path, options):
        self._imageObjects = []
        with tempfile.NamedTemporaryFile(suffix=".tiff") as temp:
            super()._writeDataToFile(data, temp.name, options)
        # if not options.get("multipage"):
        #     self._imageObjects = self._imageObjects[0]
        imageObjects = self._imageObjects
        del self._imageObjects
        return imageObjects

    def _saveImageDataToFile(self, imageData, imagePath):
        obj = self._getObjectForData(imageData)
        self._imageObjects.append(obj)

    def _getObjectForData(self, data):
        raise NotImplementedError


class PILContext(BaseImageObjectContext):

    fileExtensions = ["PIL"]

    def _getObjectForData(self, data):
        file = io.BytesIO(data.bytes())
        return Image.open(file)


class NSImageContext(BaseImageObjectContext):

    fileExtensions = ["NSImage"]

    def _getObjectForData(self, data):
        return AppKit.NSImage.alloc().initWithData_(data)
