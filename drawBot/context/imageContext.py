from __future__ import absolute_import, division

import AppKit
import Quartz

import os

from .pdfContext import PDFContext


class ImageContext(PDFContext):

    _saveImageFileTypes = {
        "jpg": AppKit.NSJPEGFileType,
        "jpeg": AppKit.NSJPEGFileType,
        "tiff": AppKit.NSTIFFFileType,
        "tif": AppKit.NSTIFFFileType,
        # "gif": AppKit.NSGIFFileType,
        "png": AppKit.NSPNGFileType,
        "bmp": AppKit.NSBMPFileType
    }

    fileExtensions = _saveImageFileTypes.keys()

    def _writeDataToFile(self, data, path, multipage, options):
        if multipage is None:
            multipage = False
        fileName, fileExt = os.path.splitext(path)
        ext = fileExt[1:]
        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
        firstPage = 0
        pageCount = pdfDocument.pageCount()
        pathAdd = "_1"
        if not multipage:
            firstPage = pageCount - 1
            pathAdd = ""
        outputPaths = []
        imageResolution = options.get("imageResolution", 72.0)
        for index in range(firstPage, pageCount):
            pool = AppKit.NSAutoreleasePool.alloc().init()
            try:
                page = pdfDocument.pageAtIndex_(index)
                image = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
                imageRep = _makeBitmapImageRep(image, imageResolution)
                imageData = imageRep.representationUsingType_properties_(self._saveImageFileTypes[ext], None)
                imagePath = fileName + pathAdd + fileExt
                imageData.writeToFile_atomically_(imagePath, True)
                pathAdd = "_%s" % (index + 2)
                outputPaths.append(imagePath)
                del page, imageRep, imageData
            finally:
                del pool
        return outputPaths


def _makeBitmapImageRep(image, imageResolution=72.0):
    """Construct a bitmap image representation at a given resolution."""
    scaleFactor = max(1.0, imageResolution) / 72.0
    rep = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None,                                   # planes
        int(image.size().width * scaleFactor),  # pixelsWide
        int(image.size().height * scaleFactor), # pixelsHigh
        8,                                      # bitsPerSample
        4,                                      # samplesPerPixel
        True,                                   # hasAlpha
        False,                                  # isPlanar
        AppKit.NSDeviceRGBColorSpace,           # colorSpaceName
        0,                                      # bytesPerRow
        0                                       # bitsPerPixel
    )
    rep.setSize_(image.size())

    AppKit.NSGraphicsContext.saveGraphicsState()
    try:
        AppKit.NSGraphicsContext.setCurrentContext_(
            AppKit.NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep))
        image.drawAtPoint_fromRect_operation_fraction_((0, 0), AppKit.NSZeroRect, AppKit.NSCompositeSourceOver, 1.0)
    finally:
        AppKit.NSGraphicsContext.restoreGraphicsState()
    return rep
