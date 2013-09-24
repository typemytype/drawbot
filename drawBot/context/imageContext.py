from AppKit import *
from Quartz import PDFDocument
import os

from pdfContext import PDFContext

class ImageContext(PDFContext):

    _saveImageFileTypes = {
        "jpg" : NSJPEGFileType,
        "jpeg" : NSJPEGFileType,
        "tiff" : NSTIFFFileType,
        "tif" : NSTIFFFileType,
        "gif" : NSGIFFileType,
        "png" : NSPNGFileType,
        "bmp" : NSBMPFileType
        }

    fileExtensions = _saveImageFileTypes.keys()

    def _writeDataToFile(self, data, path):
        fileName, ext = os.path.splitext(path)
        ext = ext[1:]
        pdfDocument = PDFDocument.alloc().initWithData_(data)
        page = pdfDocument.pageAtIndex_(pdfDocument.pageCount()-1)
        image = NSImage.alloc().initWithData_(page.dataRepresentation())
        imageRep = NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
        imageData = imageRep.representationUsingType_properties_(self._saveImageFileTypes[ext], None)
        imageData.writeToFile_atomically_(path, True)