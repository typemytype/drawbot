import AppKit
import Quartz

import os

from .pdfContext import PDFContext
from .baseContext import Color
from drawBot.misc import DrawBotError


def _nsDataConverter(value):
    if isinstance(value, AppKit.NSData):
        return value
    return AppKit.NSData.dataWithBytes_length_(value, len(value))


def _nsColorConverter(color):
    if isinstance(color, AppKit.NSColor):
        return color
    color = Color(*color)
    return color.getNSObject()


def _tiffCompressionConverter(value):
    if value is None:
        return AppKit.NSTIFFCompressionNone
    elif isinstance(value, int):
        return value
    else:
        t = dict(lzw=AppKit.NSTIFFCompressionLZW, packbits=AppKit.NSTIFFCompressionPackBits)
        return t.get(value.lower(), AppKit.NSTIFFCompressionNone)


_nsImageOptions = {
    # DrawBot Key                   NSImage property key                    converter or None          doc
    "imageColorSyncProfileData":    (AppKit.NSImageColorSyncProfileData,    _nsDataConverter,          "A bytes or NSData object containing the ColorSync profile data."),
    "imageTIFFCompressionMethod":   (AppKit.NSImageCompressionMethod,       _tiffCompressionConverter, "None, or 'lzw' or 'packbits', or an NSTIFFCompression constant"),
    "imagePNGGamma":                (AppKit.NSImageGamma,                   None,                      "The gamma value for the image. It is a floating-point number between 0.0 and 1.0, with 0.0 being black and 1.0 being the maximum color."),
    "imagePNGInterlaced":           (AppKit.NSImageInterlaced,              None,                      "Boolean value that indicates whether the image should be interlaced."),  # XXX doesn't seem to work
    "imageJPEGCompressionFactor":   (AppKit.NSImageCompressionFactor,       None,                      "A float between 0.0 and 1.0, with 1.0 resulting in no compression and 0.0 resulting in the maximum compression possible"),  # number
    "imageJPEGProgressive":         (AppKit.NSImageProgressive,             None,                      "Boolean that indicates whether the image should use progressive encoding."),
    # "imageJPEGEXIFData":          (AppKit.NSImageEXIFData,                None,                      ""),  # dict  XXX Doesn't seem to work
    "imageFallbackBackgroundColor": (AppKit.NSImageFallbackBackgroundColor, _nsColorConverter,         "The background color to use when writing to an image format (such as JPEG) that doesn't support alpha. The color's alpha value is ignored. The default background color, when this property is not specified, is white. The value of the property should be an NSColor object or a DrawBot RGB color tuple."),
    "imageGIFDitherTransparency":   (AppKit.NSImageDitherTransparency,      None,                      "Boolean that indicates whether the image is dithered"),
    "imageGIFRGBColorTable":        (AppKit.NSImageRGBColorTable,           _nsDataConverter,          "A bytes or NSData object containing the RGB color table."),
}


def getSaveImageOptions(options):
    return ImageContext.saveImageOptions + [
        (dbKey, _nsImageOptions[dbKey][-1]) for dbKey in options if dbKey in _nsImageOptions
    ]


class ImageContext(PDFContext):

    _saveImageFileTypes = {
        "jpg": AppKit.NSJPEGFileType,
        "jpeg": AppKit.NSJPEGFileType,
        "tiff": AppKit.NSTIFFFileType,
        "tif": AppKit.NSTIFFFileType,
        "gif": AppKit.NSGIFFileType,
        "png": AppKit.NSPNGFileType,
        "bmp": AppKit.NSBMPFileType
    }
    fileExtensions = []

    saveImageOptions = [
        ("imageResolution", "The resolution of the output image in PPI. Default is 72."),
        ("antiAliasing", "Indicate if a the image should be rendedered with anti-aliasing. Default is True."),
        ("multipage", "Output a numbered image for each page or frame in the document."),
    ]

    ensureEvenPixelDimensions = False

    def _writeDataToFile(self, data, path, options):
        multipage = options.get("multipage")
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
        imageResolution = options.get("imageResolution", 72.0)
        antiAliasing = options.get("antiAliasing", True)
        properties = {}
        for key, value in options.items():
            if key in _nsImageOptions:
                nsKey, converter, _ = _nsImageOptions[key]
                if converter is not None:
                    value = converter(value)
                properties[nsKey] = value
        for index in range(firstPage, pageCount):
            pool = AppKit.NSAutoreleasePool.alloc().init()
            try:
                page = pdfDocument.pageAtIndex_(index)
                imageRep = _makeBitmapImageRep(
                    pdfPage=page,
                    antiAliasing=antiAliasing,
                    imageResolution=imageResolution
                )
                if self.ensureEvenPixelDimensions:
                    if imageRep.pixelsWide() % 2 or imageRep.pixelsHigh() % 2:
                        raise DrawBotError("Exporting to %s doesn't support odd pixel dimensions for width and height." % (", ".join(self.fileExtensions)))
                imageData = imageRep.representationUsingType_properties_(self._saveImageFileTypes[ext], properties)
                imagePath = fileName + pathAdd + fileExt
                self._storeImageData(imageData, imagePath)
                pathAdd = "_%s" % (index + 2)
                del page, imageRep, imageData
            finally:
                del pool

    def _storeImageData(self, imageData, imagePath):
        imageData.writeToFile_atomically_(imagePath, True)


def _makeBitmapImageRep(nsImage=None, pdfPage=None, imageResolution=72.0, antiAliasing=True, colorSpaceName=AppKit.NSCalibratedRGBColorSpace):
    """Construct a bitmap image representation at a given resolution."""
    if nsImage is None and pdfPage is None:
        raise DrawBotError("At least a image or a pdf page must be provided to create a bitmap representaion.")
    scaleFactor = max(1.0, imageResolution) / 72.0
    if pdfPage is not None:
        mediaBox = pdfPage.boundsForBox_(Quartz.kPDFDisplayBoxMediaBox)
        width, height = mediaBox.size
    elif nsImage is not None:
        width, height = nsImage.size()

    rep = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None,                                    # planes
        int(width * scaleFactor),                # pixelsWide
        int(height * scaleFactor),               # pixelsHigh
        8,                                       # bitsPerSample
        4,                                       # samplesPerPixel
        True,                                    # hasAlpha
        False,                                   # isPlanar
        colorSpaceName,                          # colorSpaceName
        0,                                       # bytesPerRow
        0                                        # bitsPerPixel
    )

    rep.setSize_((width, height))

    AppKit.NSGraphicsContext.saveGraphicsState()
    try:
        AppKit.NSGraphicsContext.setCurrentContext_(
            AppKit.NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep))
        if pdfPage is not None:
            context = AppKit.NSGraphicsContext.currentContext().CGContext()
            if not antiAliasing:
                Quartz.CGContextSetInterpolationQuality(context, Quartz.kCGInterpolationNone)
                Quartz.CGContextSetAllowsAntialiasing(context, False)
            Quartz.CGContextDrawPDFPage(context, pdfPage.pageRef())
        elif nsImage is not None:
            nsImage.drawAtPoint_fromRect_operation_fraction_((0, 0), AppKit.NSZeroRect, AppKit.NSCompositeSourceOver, 1.0)
    finally:
        AppKit.NSGraphicsContext.restoreGraphicsState()
    return rep


# ================================
# = contexts for file extensions =
# ================================

class JPEGContext(ImageContext):

    fileExtensions = ["jpg", "jpeg"]

    saveImageOptions = getSaveImageOptions([
        "imageJPEGCompressionFactor",
        "imageJPEGProgressive",
        "imageFallbackBackgroundColor",
        "imageColorSyncProfileData",
    ])


class BMPContext(ImageContext):

    fileExtensions = ["bmp"]


class PNGContext(ImageContext):

    fileExtensions = ["png"]

    saveImageOptions = getSaveImageOptions([
        "imagePNGGamma",
        "imagePNGInterlaced",
        "imageColorSyncProfileData",
    ])


class TIFFContext(ImageContext):

    fileExtensions = ["tif", "tiff"]

    saveImageOptions = getSaveImageOptions([
        "imageTIFFCompressionMethod",
        "imageColorSyncProfileData",
    ])
