from __future__ import absolute_import

from .imageContext import ImageContext, getSaveImageOptions


class PNGContext(ImageContext):

    fileExtensions = ["png"]

    saveImageOptions = getSaveImageOptions([
        "imagePNGGamma",
        "imagePNGInterlaced"
    ])
