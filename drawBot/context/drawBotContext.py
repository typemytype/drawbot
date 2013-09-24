## read the docs hack
try:
    from Quartz import *
except:
    pass

from pdfContext import PDFContext

class DrawBotContext(PDFContext):

    def getNSPDFDocument(self):
        if not self._hasContext:
            return None
        CGPDFContextEndPage(self._pdfContext)
        CGPDFContextClose(self._pdfContext)        
        doc = PDFDocument.alloc().initWithData_(self._pdfData)
        self._hasContext = False
        self._pdfContext = None
        self._pdfData = None
        return doc