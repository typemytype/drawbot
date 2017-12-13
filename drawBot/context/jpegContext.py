from __future__ import absolute_import

from .imageContext import ImageContext, getSaveImageOptions


class JpegContext(ImageContext):

    fileExtensions = ["jpg", "jgeg"]

    saveImageOptions = getSaveImageOptions([
        "imageJPEGCompressionFactor",
        "imageJPEGProgressive",
        "imageFallbackBackgroundColor"
    ])
