import AppKit
from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController

from .codeEditor import CodeEditor, OutPutEditor
from .drawView import DrawView, ThumbnailView

from drawBot.scriptTools import ScriptRunner, CallbackRunner, StdOutput
from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.drawBotContext import DrawBotContext
from drawBot.misc import getDefault, setDefault, warnings

from .splitView import SplitView


class DrawBotController(BaseWindowController):

    """
    The controller for a DrawBot window.
    """

    windowAutoSaveName = "DrawBotController"

    def __init__(self):
        # make a window
        self.w = Window((400, 400), "DrawBot", minSize=(200, 200), textured=False, autosaveName=self.windowAutoSaveName)
        # setting previously stored frames, if any
        self.w.getNSWindow().setFrameUsingName_(self.windowAutoSaveName)
        try:
            # on 10.7+ full screen support
            self.w.getNSWindow().setCollectionBehavior_(128)  # NSWindowCollectionBehaviorFullScreenPrimary
        except:
            pass

        # the code editor
        self.codeView = CodeEditor((0, 0, -0, -0), callback=self.codeViewCallback)
        # the output view (will catch all stdout and stderr)
        self.outPutView = OutPutEditor((0, 0, -0, -0), readOnly=True)
        # the view to draw in
        self.drawView = DrawView((0, 0, -0, -0))
        # the view with all thumbnails
        self.thumbnails = ThumbnailView((0, 0, -0, -0))
        # connect the thumbnail view with the draw view
        self.thumbnails.setDrawView(self.drawView)

        # collect all code text view in a splitview
        paneDescriptors = [
            dict(view=self.codeView, identifier="codeView", minSize=50, canCollapse=False),
            dict(view=self.outPutView, identifier="outPutView", size=100, minSize=50, canCollapse=False),
        ]
        self.codeSplit = SplitView((0, 0, -0, -0), paneDescriptors, isVertical=False)

        # collect the draw scroll view and the code split view in a splitview
        paneDescriptors = [
            dict(view=self.thumbnails, identifier="thumbnails", minSize=100, size=100, maxSize=100),
            dict(view=self.drawView, identifier="drawView", minSize=50),
            dict(view=self.codeSplit, identifier="codeSplit", minSize=50, canCollapse=False),
        ]
        self.w.split = SplitView((0, 0, -0, -0), paneDescriptors)

        # setup BaseWindowController base behavoir
        self.setUpBaseWindowBehavior()

        # get the real size of the window
        windowX, windowY, windowWidth, windowHeight = self.w.getPosSize()
        # set the split view dividers at a specific position based on the window size
        self.w.split.setDividerPosition(0, 0)
        self.w.split.setDividerPosition(1, windowWidth * .6)
        self.codeSplit.setDividerPosition(0, windowHeight * .7)

        if getDefault("DrawBotAddToolbar", True):
            # add toolbar
            self.addToolbar()

    def codeViewCallback(self, sender):
        document = self.w.getNSWindowController().document()
        document.updateChangeCount_(AppKit.NSChangeDone)

    def runCode(self, liveCoding=False):
        # get the code
        code = self.code()
        # code = code.encode("utf-8")
        # save the code in the defaults, if something goes wrong
        setDefault("DrawBotCodeBackup", code)
        # get te path of the document (will be None for an untitled document)
        path = self.path()
        # reset the internal warning system
        warnings.resetWarnings()
        # reset the drawing tool
        _drawBotDrawingTool.newDrawing()
        # create a namespace
        namespace = {}
        # add the tool callbacks in the name space
        _drawBotDrawingTool._addToNamespace(namespace)
        # when enabled clear the output text view
        if getDefault("DrawBotClearOutput", True):
            self.outPutView.clear()
        # create a new std output, catching all print statements and tracebacks
        self.output = []

        liveOutput = None
        if getDefault("DrawButLiveUpdateStdoutStderr", False):
            liveOutput = self.outPutView

        self.stdout = StdOutput(self.output, outputView=liveOutput)
        self.stderr = StdOutput(self.output, isError=True, outputView=liveOutput)
        # warnings should show the warnings
        warnings.shouldShowWarnings = True
        # run the code
        ScriptRunner(code, path, namespace=namespace, stdout=self.stdout, stderr=self.stderr)
        # warnings should stop posting them
        warnings.shouldShowWarnings = False
        # set context, only when the panes are visible
        if self.w.split.isPaneVisible("drawView") or self.w.split.isPaneVisible("thumbnails"):
            def createContext(context):
                # draw the tool in to the context
                _drawBotDrawingTool._drawInContext(context)
            # create a context to draw in
            context = DrawBotContext()
            # savely run the callback and track all traceback back the output
            CallbackRunner(createContext, stdout=self.stdout, stderr=self.stderr, args=[context])
            # get the pdf document and set in the draw view
            pdfDocument = context.getNSPDFDocument()
            selectionIndex = self.thumbnails.getSelection()
            if not liveCoding or (pdfDocument and pdfDocument.pageCount()):
                self.drawView.setPDFDocument(pdfDocument)
            # scroll to the original position
            self.drawView.scrollToPageIndex(selectionIndex)
        else:
            # if the panes are not visible, clear the draw view
            self.drawView.setPDFDocument(None)
        # drawing is done
        _drawBotDrawingTool.endDrawing()
        # set the catched print statements and tracebacks in the the output text view
        for text, isError in self.output:
            if liveCoding and isError:
                continue
            self.outPutView.append(text, isError)

        # reset the code backup if the script runs with any crashes
        setDefault("DrawBotCodeBackup", None)
        # clean up

        self.output = None
        self.stdout = None
        self.stderr = None

    def checkSyntax(self, sender=None):
        # get the code
        code = self.code()
        # get te path of the document (will be None for an untitled document)
        path = self.path()
        # when enabled clear the output text view
        if getDefault("DrawBotClearOutput", True):
            self.outPutView.set("")
        # create a new std output, catching all print statements and tracebacks
        self.output = []
        self.stdout = StdOutput(self.output)
        self.stderr = StdOutput(self.output, True)
        # run the code, but with the optional flag checkSyntaxOnly so it will just compile the code
        ScriptRunner(code, path, stdout=self.stdout, stderr=self.stderr, checkSyntaxOnly=True)
        # set the catched print statements and tracebacks in the the output text view
        for text, isError in self.output:
            self.outPutView.append(text, isError)
        # clean up
        self.output = None
        self.stdout = None
        self.stderr = None

    def formatCode(self, sender=None):
        import black
        # get the code
        code = self.code()
        # format the code with black
        try:
            formattedCode = black.format_str(code, mode=black.Mode())
        except black.InvalidInput:
            return
        # set it back in the text view
        textView = self.codeView.getNSTextView()
        # store current selection by line range
        selectedRange = textView.selectedRange()
        string = textView.string()
        lineRange = string.lineRangeForRange_(selectedRange)
        # replace the text
        textView.insertText_replacementRange_(formattedCode, (0, string.length()))
        # try to reset the selection location back
        cursor = (lineRange.location, 0)
        try:
            textView.setSelectedRange_(cursor)
            textView.scrollRangeToVisible_(cursor)
        except IndexError:
            # fail silently
            pass

    def _savePDF(self, path):
        # get the pdf date from the draw view
        data = self.drawView.get()
        if data:
            # if there is date save it
            data.writeToFile_atomically_(path, False)

    def savePDF(self, sender=None):
        """
        Save the content as a pdf.
        """
        # pop up a show put file sheet
        self.showPutFile(["pdf"], callback=self._savePDF)

    def setPath(self, path):
        """
        Sets the content of a file into the code view.
        """
        # open a file
        f = open(path, "rb")
        # read the content
        code = f.read().decode("utf-8")
        # close the file
        f.close()
        # set the content into the code view
        self.codeView.set(code)

    def path(self):
        """
        Returns the path of the document,
        return None if the document is never saved before.
        """
        # get the docuemnt
        document = self.document()
        # check if it is not None
        if document is None:
            return None
        # get the url of the document
        url = document.fileURL()
        if url is None:
            return None
        # return the path as a string
        return url.path()

    def code(self):
        """
        Returns the content of the code view as a string.
        """
        return self.codeView.get()

    def setCode(self, code):
        """
        Sets code in to the code view.
        """
        self.codeView.set(code)

    def pdfData(self):
        """
        Returns the pdf data from the draw view
        """
        return self.drawView.get()

    # UI

    def open(self):
        # open the window
        self.w.open()
        # set the code view as first responder
        self.w.getNSWindow().makeFirstResponder_(self.codeView.getNSTextView())

    def assignToDocument(self, nsDocument):
        # assing the window to the document
        self.w.assignToDocument(nsDocument)

    def document(self):
        """
        Returns the document.
        """
        return self.w.getNSWindow().document()

    def setUpBaseWindowBehavior(self):
        # bind whenever a user moves or resizes a window
        self.w.bind("move", self.windowMoveCallback)
        self.w.bind("resize", self.windowResizeCallback)
        super(DrawBotController, self).setUpBaseWindowBehavior()

    def windowMoveCallback(self, sender):
        # save the frame in the defaults
        self.w.getNSWindow().saveFrameUsingName_(self.windowAutoSaveName)

    def windowResizeCallback(self, sender):
        # save the frame in the defaults
        self.w.getNSWindow().saveFrameUsingName_(self.windowAutoSaveName)

    def windowCloseCallback(self, sender):
        # unbind on window close
        self.w.unbind("move", self.windowMoveCallback)
        self.w.unbind("resize", self.windowResizeCallback)
        super(DrawBotController, self).windowCloseCallback(sender)

    def addToolbar(self):
        toolbarItems = [
            dict(
                itemIdentifier="run",
                label="Run",
                imageNamed="toolbarRun",
                imageTemplate=True,
                callback=self.toolbarRun,
            ),
            dict(
                itemIdentifier="comment",
                label="Comment",
                imageNamed="toolbarComment",
                imageTemplate=True,
                callback=self.toolbarComment,
            ),
            dict(
                itemIdentifier="uncomment",
                label="Uncomment",
                imageNamed="toolbarUncomment",
                imageTemplate=True,
                callback=self.toolbarUncomment,
            ),
            dict(
                itemIdentifier="indent",
                label="Indent",
                imageNamed="toolbarIndent",
                imageTemplate=True,
                callback=self.toolbarIndent,
            ),
            dict(
                itemIdentifier="dedent",
                label="Dedent",
                imageNamed="toolbarDedent",
                imageTemplate=True,
                callback=self.toolbarDedent,
            ),
        ]
        self.w.addToolbar(toolbarIdentifier="DrawBotToolbar", toolbarItems=toolbarItems, addStandardItems=False)

    def toolbarRun(self, sender):
        self.runCode()

    def toolbarComment(self, sender):
        self.codeView.comment()

    def toolbarUncomment(self, sender):
        self.codeView.uncomment()

    def toolbarIndent(self, sender):
        self.codeView.indent()

    def toolbarDedent(self, sender):
        self.codeView.dedent()
