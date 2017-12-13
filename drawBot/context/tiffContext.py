from __future__ import absolute_import

from .imageContext import ImageContext, getSaveImageOptions


class TIFFContext(ImageContext):

    fileExtensions = ["tif", "tiff"]

    saveImageOptions = getSaveImageOptions([
        "imageTIFFCompressionMethod"
    ])
