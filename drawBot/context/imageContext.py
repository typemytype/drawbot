from __future__ import absolute_import

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
        for index in range(firstPage, pageCount):
            pool = AppKit.NSAutoreleasePool.alloc().init()
            try:
                page = pdfDocument.pageAtIndex_(index)
                image = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
                imageRep = _unscaledBitmapImageRep(image)
                imageData = imageRep.representationUsingType_properties_(self._saveImageFileTypes[ext], None)
                imagePath = fileName + pathAdd + fileExt
                imageData.writeToFile_atomically_(imagePath, True)
                pathAdd = "_%s" % (index + 2)
                outputPaths.append(imagePath)
                del page, imageRep, imageData
            finally:
                del pool
        return outputPaths


def _unscaledBitmapImageRep(image):
    """Construct a bitmap image representation of 72 DPI, regardless of what kind of display is active."""
    rep = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None,                         # planes
        int(image.size().width),      # pixelsWide
        int(image.size().height),     # pixelsHigh
        8,                            # bitsPerSample
        4,                            # samplesPerPixel
        True,                         # hasAlpha
        False,                        # isPlanar
        AppKit.NSDeviceRGBColorSpace, # colorSpaceName
        0,                            # bytesPerRow
        0                             # bitsPerPixel
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
