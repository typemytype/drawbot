from __future__ import absolute_import

from .imageContext import ImageContext, getSaveImageOptions


class PngContext(ImageContext):

    fileExtensions = ["png"]

    saveImageOptions = getSaveImageOptions([
        "imagePNGGamma",
        "imagePNGInterlaced"
    ])
