from pdfContext import PDFContext
from imageContext import ImageContext
from gifContext import GifContext
from svgContext import SVGContext
from movContext import MOVContext
from printContext import PrintContext


allContexts = (PDFContext, ImageContext, SVGContext, MOVContext, PrintContext, GifContext)


def getContextForFileExt(ext):
    for context in allContexts:
        if ext in context.fileExtensions:
            return context()
    return None
