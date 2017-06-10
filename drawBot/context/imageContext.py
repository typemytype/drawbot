import AppKit
import Quartz

import os

from pdfContext import PDFContext


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

    def _writeDataToFile(self, data, path, multipage):
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
            page = pdfDocument.pageAtIndex_(index)
            image = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
            imageRep = AppKit.NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
            imageData = imageRep.representationUsingType_properties_(self._saveImageFileTypes[ext], None)
            imagePath = fileName + pathAdd + fileExt
            imageData.writeToFile_atomically_(imagePath, True)
            pathAdd = "_%s" % (index + 2)
            outputPaths.append(imagePath)
            del page, imageRep, imageData
            del pool
        return outputPaths
