from __future__ import absolute_import

from .pdfContext import PDFContext
from .pngContext import PNGContext
from .jpegContext import JPEGContext
from .tiffContext import TIFFContext
from .gifContext import GIFContext
from .bmpContext import BMPContext
from .svgContext import SVGContext
from .movContext import MOVContext
from .printContext import PrintContext
from .mp4Context import MP4Context


allContexts = [
    PDFContext,
    PNGContext,
    JPEGContext,
    TIFFContext,
    SVGContext,
    GIFContext,
    BMPContext,
    MP4Context,
    MOVContext,
    PrintContext
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
            docs.append("*%s*:" % ext)
            docs.append("")
            for key, doc in context.saveImageOptions:
                docs.append(formatter % (key, doc))
            docs.append("")
    return docs

# def getContextOptionsDocs():
#     docs = []
#     done = set()
#     formatter = "* `%s`: %s"
#     emptyDocFormatter = "* `%s`"
#     for context in allContexts:
#         if context.saveImageOptions:
#             for key, doc in context.saveImageOptions:
#                 if key in done:
#                     continue
#                 if doc:
#                     value = formatter % (key, doc)
#                 else:
#                     value = emptyDocFormatter % key
#                 docs.append(value)
#                 done.add(key)
#     return docs