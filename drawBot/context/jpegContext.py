from __future__ import absolute_import

from .imageContext import ImageContext, getSaveImageOptions


class JPEGContext(ImageContext):

    fileExtensions = ["jpg", "jgeg"]

    saveImageOptions = getSaveImageOptions([
        "imageJPEGCompressionFactor",
        "imageJPEGProgressive",
        "imageFallbackBackgroundColor"
    ])
