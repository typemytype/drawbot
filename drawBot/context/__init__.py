from __future__ import absolute_import

from .pdfContext import PDFContext
from .imageContext import ImageContext
from .gifContext import GifContext
from .svgContext import SVGContext
from .movContext import MOVContext
from .printContext import PrintContext
from .mp4Context import MP4Context


allContexts = [PDFContext, ImageContext, SVGContext, MOVContext, GifContext, MP4Context, PrintContext]


def subscribeContext(context):
    for ctx in list(allContexts):
        if ctx.__name__ == context.__name__:
            allContexts.remove(ctx)
    allContexts.append(context)


def getContextForFileExt(ext):
    for context in allContexts:
        if ext in context.fileExtensions:
            return context()
    return None
