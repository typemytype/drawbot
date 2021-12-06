from .pdfContext import PDFContext
from .imageContext import PNGContext, JPEGContext, TIFFContext, BMPContext
from .gifContext import GIFContext
from .svgContext import SVGContext
from .printContext import PrintContext
from .mp4Context import MP4Context
from .icnsContext import ICNSContext
from .imageObjectContext import PILContext, NSImageContext


allContexts = [
    PDFContext,
    PNGContext,
    JPEGContext,
    TIFFContext,
    SVGContext,
    GIFContext,
    BMPContext,
    MP4Context,
    ICNSContext,
    PrintContext,
    PILContext,
    NSImageContext,
]


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


def getContextOptions():
    options = set()
    for context in allContexts:
        for key, _ in context.saveImageOptions:
            options.add(key)
    return options


def getFileExtensions():
    extensions = []
    for context in allContexts:
        for ext in context.fileExtensions:
            if ext not in extensions:
                extensions.append(ext)
    return extensions


def getContextOptionsDocs(formatter="* `%s`: %s"):
    docs = []
    for context in allContexts:
        if context.saveImageOptions:
            ext = ", ".join(context.fileExtensions)
            docs.append("*%s options:*" % ext)
            docs.append("")
            for key, doc in context.saveImageOptions:
                docs.append(formatter % (key, doc))
            docs.append("")
    return docs
