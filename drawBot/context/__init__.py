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
    done = set()
    for context in allContexts:
        for key, doc in context.saveImageOptions:
            if key in done:
                continue
            docs.append(formatter % (key, doc))
            done.add(key)
    return docs
