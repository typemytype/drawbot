import Quartz

from .pdfContext import PDFContext


class DrawBotContext(PDFContext):

    def getNSPDFDocument(self):
        if not self._hasContext:
            return None
        Quartz.CGPDFContextEndPage(self._pdfContext)
        Quartz.CGPDFContextClose(self._pdfContext)
        doc = Quartz.PDFDocument.alloc().initWithData_(self._pdfData)
        self._hasContext = False
        self._pdfContext = None
        self._pdfData = None
        return doc
