from Foundation import NSURL
from AppKit import NSDragOperationNone, NSBezelBorder
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

    def getSelection(self):
        try:
            # sometimes this goes weirdly wrong...
            selection = self.getNSView().selectedPages()
        except:
            return -1
        if selection:
            for page in selection:
                document = page.document()
                index = document.indexForPage_(page)
                return index
        return -1


class DrawBotPDFView(PDFView):

    def performKeyEquivalent_(self, event):
        # catch a bug in PDFView
        # cmd + ` causes a traceback
        # DrawBot[15705]: -[__NSCFConstantString characterAtIndex:]: Range or index out of bounds
        try:
            return super(DrawBotPDFView, self).performKeyEquivalent_(event)
        except:
            return False


class DrawView(Group):

    nsViewClass = DrawBotPDFView

    def __init__(self, posSize):
        super(DrawView, self).__init__(posSize)
        pdfView = self.getNSView()
        pdfView.setAutoScales_(True)
        view = pdfView.documentView()
        if view is not None:
            scrollview = view.enclosingScrollView()
            scrollview.setBorderType_(NSBezelBorder)

    def get(self):
        pdf = self.getNSView().document()
        if pdf is None:
            return None
        return pdf.dataRepresentation()

    def set(self, pdfData):
        pdf = PDFDocument.alloc().initWithData_(pdfData)
        self.setPDFDocument(pdf)

    def setPath(self, path):
        url = NSURL.fileURLWithPath_(path)
        document = PDFDocument.alloc().initWithURL_(url)
        self.setPDFDocument(document)

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

    def scrollToPageIndex(self, index):
        pdf = self.getPDFDocument()
        if pdf is None:
            self.scrollDown()
        elif 0 <= index < pdf.pageCount():
            try:
                # sometimes this goes weirdly wrong...
                page = pdf.pageAtIndex_(index)
                self.getNSView().goToPage_(page)
            except:
                self.scrollDown()
        else:
            self.scrollDown()
