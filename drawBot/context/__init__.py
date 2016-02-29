from pdfContext import PDFContext
from imageContext import ImageContext
from gifContext import GifContext
from svgContext import SVGContext
from movContext import MOVContext
from printContext import PrintContext


allContexts = (PDFContext, ImageContext, SVGContext, MOVContext, PrintContext, GifContext)


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
