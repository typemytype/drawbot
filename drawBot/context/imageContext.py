import AppKit
import Quartz

import os

from pdfContext import PDFContext

class ImageContext(PDFContext):

    _saveImageFileTypes = {
        "jpg" : AppKit.NSJPEGFileType,
        "jpeg" : AppKit.NSJPEGFileType,
        "tiff" : AppKit.NSTIFFFileType,
        "tif" : AppKit.NSTIFFFileType,
        "gif" : AppKit.NSGIFFileType,
        "png" : AppKit.NSPNGFileType,
        "bmp" : AppKit.NSBMPFileType
        }

    fileExtensions = _saveImageFileTypes.keys()

    def _writeDataToFile(self, data, path):
        fileName, ext = os.path.splitext(path)
        ext = ext[1:]
        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
        page = pdfDocument.pageAtIndex_(pdfDocument.pageCount()-1)
        image = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
        imageRep = AppKit.NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
        imageData = imageRep.representationUsingType_properties_(self._saveImageFileTypes[ext], None)
        imageData.writeToFile_atomically_(path, True)