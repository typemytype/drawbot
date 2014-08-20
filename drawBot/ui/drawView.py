from AppKit import *
from Quartz import PDFView, PDFThumbnailView, PDFDocument

from vanilla import Group

epsPasteBoardType = "CorePasteboardFlavorType 0x41494342"

class DrawBotPDFThumbnailView(PDFThumbnailView):

    def draggingUpdated_(self, draggingInfo):
        return NSDragOperationNone

class ThumbnailView(Group):

    nsViewClass = DrawBotPDFThumbnailView

    def setDrawView(self, view):
        self.getNSView().setPDFView_(view.getNSView())

class DrawView(Group):

    nsViewClass = PDFView

    def __init__(self, posSize):
        super(DrawView, self).__init__(posSize)
        pdfView = self.getNSView()
        pdfView.setAutoScales_(True)
        view = pdfView.documentView()
        scrollview = view.enclosingScrollView()
        scrollview.setBorderType_(NSBezelBorder)

    def get(self):
        pdf = self.getNSView().document()
        if pdf is None:
            return None
        return pdf.dataRepresentation()

    def set(self, pdfData):
        pdf = PDFDocument.alloc().initWithData_(self._pdfData)
        self.setPDFDocument(pdf)

    def setPDFDocument(self, document):
        if document is None:
            document = PDFDocument.alloc().init()
        self.getNSView().setDocument_(document)

    def getPDFDocument(self):
        return self.getNSView().document()

    def setScale(self, scale):
        self.getNSView().setScaleFactor_(scale)

    def scale(self):
        return self.getNSView().scaleFactor()

    def scrollDown(self):
        document = self.getNSView().documentView()
        document.scrollPoint_((0, 0))