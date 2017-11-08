import AppKit
from PyObjCTools import AppHelper

import os
from random import randint

from drawBot.ui.drawBotController import DrawBotController
from drawBot.ui.preferencesController import PreferencesController
from drawBot.ui.debug import DebugWindowController

import drawBot.drawBotDrawingTools
from drawBot.misc import getDefault, stringToInt
from drawBot.updater import Updater

import objc

objc.setVerbose(True)


class DrawBotDocument(AppKit.NSDocument):

    def readFromFile_ofType_(self, path, tp):
        return True, None

    def writeSafelyToURL_ofType_forSaveOperation_error_(self, url, fileType, saveOperation, error):
        path = url.path()
        code = self.vanillaWindowController.code()
        f = file(path, "w")
        f.write(code.encode("utf8"))
        f.close()
        self._modDate = self.getModificationDate(path)
        return True, None

    def makeWindowControllers(self):
        self.vanillaWindowController = DrawBotController()
        wc = self.vanillaWindowController.w.getNSWindowController()
        self.addWindowController_(wc)
        wc.setShouldCloseDocument_(True)

        url = self.fileURL()
        if url:
            self.vanillaWindowController.setPath(url.path())
        self.vanillaWindowController.open()
        self._modDate = self.getModificationDate()

    # main menu callbacks

    def runCode_(self, sender):
        liveCoding = False
        if hasattr(sender, "isLiveCoding"):
            liveCoding = sender.isLiveCoding()
        self.vanillaWindowController.runCode(liveCoding)
        return True

    def checkSyntax_(self, sender):
        self.vanillaWindowController.checkSyntax()
        return True

    def saveDocumentAsPDF_(self, sender):
        self.vanillaWindowController.savePDF()
        return True

    def validateMenuItem_(self, menuItem):
        if menuItem.action() in ("saveDocumentAsPDF:"):
            return self.vanillaWindowController.pdfData() is not None
        return True

    def testForExternalChanges(self):
        if self._modDate is None:
            return
        url = self.fileURL()
        if url is None:
            return
        path = url.path()

        modDate = self.getModificationDate()
        if modDate > self._modDate:
            def _update(value):
                if value:
                    self.vanillaWindowController.setPath(path)

            if self.isDocumentEdited():
                self.vanillaWindowController.showAskYesNo("External Change", "Update this un-saved document.", _update)
            else:
                _update(True)
            self._modDate = modDate

    def getModificationDate(self, path=None):
        if path is None:
            url = self.fileURL()
            if url is None:
                return None
            path = url.path()
        fm = AppKit.NSFileManager.defaultManager()
        attr, error = fm.attributesOfItemAtPath_error_(path, None)
        if attr is None:
            return None
        return attr.fileModificationDate()


class DrawBotAppDelegate(AppKit.NSObject):

    def init(self):
        self = super(DrawBotAppDelegate, self).init()
        code = stringToInt(b"GURL")
        AppKit.NSAppleEventManager.sharedAppleEventManager().setEventHandler_andSelector_forEventClass_andEventID_(self, "getUrl:withReplyEvent:", code, code)
        return self

    def applicationDidFinishLaunching_(self, notification):
        self._debugger = DebugWindowController()
        Updater()

    def applicationDidBecomeActive_(self, notification):
        for document in AppKit.NSApp().orderedDocuments():
            document.testForExternalChanges()
        self.sheduleIconTimer()
        drawBot.drawBotDrawingTools._chachedPixelColorBitmaps.clear()

    def applicationShouldOpenUntitledFile_(self, sender):
        return getDefault("shouldOpenUntitledFile", True)

    def sheduleIconTimer(self):
        if getDefault("DrawBotAnimateIcon", True):
            self._iconTimer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.1, self, "animateApplicationIcon:", None, False)

    def animateApplicationIcon_(self, timer):
        if AppKit.NSApp().isActive():
            image = AppKit.NSImage.imageNamed_("icon_%s" % randint(0, 20))
            AppKit.NSApp().setApplicationIconImage_(image)
            self.sheduleIconTimer()

    def showDocumentation_(self, sender):
        url = "http://www.drawbot.com"
        ws = AppKit.NSWorkspace.sharedWorkspace()
        ws.openURL_(AppKit.NSURL.URLWithString_(url))

    def showPreferences_(self, sender):
        try:
            self.preferencesController.show()
        except Exception:
            self.preferencesController = PreferencesController()

    def showDebug_(self, sender):
        self._debugger.showHide()

    def getUrl_withReplyEvent_(self, event, reply):
        import urlparse
        import urllib2
        code = stringToInt(b"----")
        url = event.paramDescriptorForKeyword_(code)
        urlString = url.stringValue()
        documentController = AppKit.NSDocumentController.sharedDocumentController()

        data = urlparse.urlparse(urlString)
        if data.netloc:
            # in the cloudzzz
            pythonPath = "http://%s%s" % (data.netloc, data.path)
            response = urllib2.urlopen(pythonPath)
            code = response.read()
            response.close()
        else:
            # local
            pythonPath = data.path
            f = open(pythonPath, "rb")
            code = f.read()
            f.close()
        document, error = documentController.openUntitledDocumentAndDisplay_error_(True, None)
        try:
            code = code.decode("utf-8")
        except Exception:
            pass
        document.vanillaWindowController.setCode(code)

        def result(shouldOpen):
            if not shouldOpen:
                document.close()

        fileName = os.path.basename(data.path)
        domain = data.netloc
        if not domain:
            domain = "Local"
        document.vanillaWindowController.showAskYesNo("Download External Script",
            "You opened '%s' from '%s'.\n\n"
            "Read the code before running it so you know what it will do. If you don't understand it, don't run it.\n\n"
            "Do you want to open this Script?" % (fileName, domain),
            result
        )

    def performFindPanelAction_(self, action):
        try:
            # a bug somewhere in OSX
            # the short cuts (fe cmd+g) arent redirected properly to the text views
            view = AppKit.NSApp().keyWindow().firstResponder()
            dest = view.superview().superview().superview()._contentView().documentView()
            dest.performFindPanelAction_(action)
        except Exception:
            pass


if __name__ == "__main__":
    AppHelper.runEventLoop()
