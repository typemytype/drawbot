import AppKit
from PyObjCTools import AppHelper

import sys
import os
import site
import random

from vanilla.dialogs import message

from drawBot.ui.drawBotController import DrawBotController
from drawBot.ui.preferencesController import PreferencesController
from drawBot.ui.debug import DebugWindowController
from drawBot.scriptTools import retrieveCheckEventQueueForUserCancelFromCarbon

from drawBot.ui.drawBotPackageController import DrawBotPackageController
from drawBot.misc import getDefault, stringToInt
from drawBot.updater import Updater
from drawBot.drawBotPackage import DrawBotPackage

import objc
from objc import super

objc.setVerbose(True)


class DrawBotDocument(AppKit.NSDocument):

    def readFromFile_ofType_(self, path, tp):
        return True, None

    def writeSafelyToURL_ofType_forSaveOperation_error_(self, url, fileType, saveOperation, error):
        path = url.path()
        code = self.vanillaWindowController.code()
        f = open(path, "wb")
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
        retrieveCheckEventQueueForUserCancelFromCarbon()
        self._debugger = DebugWindowController()
        Updater()
        if sys.argv[1:]:
            import re
            pat = re.compile("--testScript=(.*)")
            for arg in sys.argv[1:]:
                m = pat.match(arg)
                if m is None:
                    continue
                AppKit.NSApp().activateIgnoringOtherApps_(True)
                testScript = m.group(1)
                self.performSelector_withObject_afterDelay_("_runTestScript:", testScript, 0.25)

    def _runTestScript_(self, testScript):
        import traceback
        assert os.path.exists(testScript), "%r cannot be found" % testScript
        with open(testScript) as f:
            source = f.read()
        try:
            exec(source, {"__name__": "__main__", "__file__": testScript})
        except Exception:
            traceback.print_exc()
        AppKit.NSApp().terminate_(None)

    def applicationDidBecomeActive_(self, notification):
        for document in AppKit.NSApp().orderedDocuments():
            document.testForExternalChanges()
        self.sheduleIconTimer()

    def applicationShouldOpenUntitledFile_(self, sender):
        return getDefault("shouldOpenUntitledFile", True)

    def sheduleIconTimer(self):
        if getDefault("DrawBotAnimateIcon", True):
            self._iconTimer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.1, self, "animateApplicationIcon:", None, False)

    _iconCounter = 0
    _iconHand = random.choice(["left", "right"])

    def animateApplicationIcon_(self, timer):
        if AppKit.NSApp().isActive():
            image = AppKit.NSImage.imageNamed_("icon_%s_%s" % (self._iconHand, self._iconCounter))
            AppKit.NSApp().setApplicationIconImage_(image)
            self._iconCounter += 1
            if self._iconCounter > 20:
                self._iconCounter = 0
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

    def showForum_(self, sender):
        url = "http://forum.drawbot.com"
        ws = AppKit.NSWorkspace.sharedWorkspace()
        ws.openURL_(AppKit.NSURL.URLWithString_(url))

    def showPIPInstaller_(self, sender):
        if hasattr(self, "pipInstallerController"):
            self.pipInstallerController.show()
        else:
            from drawBot.pipInstaller import PipInstallerController
            self.pipInstallerController = PipInstallerController(_getPIPTargetPath())

    def buildPackage_(self, sender):
        DrawBotPackageController()

    def getUrl_withReplyEvent_(self, event, reply):
        from urllib.parse import urlparse
        from urllib.request import urlopen
        code = stringToInt(b"----")
        url = event.paramDescriptorForKeyword_(code)
        urlString = url.stringValue()
        documentController = AppKit.NSDocumentController.sharedDocumentController()

        data = urlparse(urlString)
        if data.netloc:
            # in the cloudzzz
            pythonPath = "http://%s%s" % (data.netloc, data.path)
            response = urlopen(pythonPath)
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

    def application_openFile_(self, app, path):
        ext = os.path.splitext(path)[-1]
        if ext.lower() == ".drawbot":
            succes, report = DrawBotPackage(path).run()
            if not succes:
                fileName = os.path.basename(path)
                message("The DrawBot package '%s' failed." % fileName, report)
            return True
        return False


def _getPIPTargetPath():
    appSupportPath = AppKit.NSSearchPathForDirectoriesInDomains(
        AppKit.NSApplicationSupportDirectory,
        AppKit.NSUserDomainMask, True)[0]
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    return os.path.join(appSupportPath, f"DrawBot/Python{version}")


def _addLocalSysPaths():
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    paths = [
        _getPIPTargetPath(),
        f'/Library/Python/{version}/site-packages',
        f'/Library/Frameworks/Python.framework/Versions/{version}/lib/python{version}/site-packages/',
    ]
    for path in paths:
        if path not in sys.path and os.path.exists(path):
            site.addsitedir(path)

_addLocalSysPaths()


if __name__ == "__main__":
    AppHelper.runEventLoop()
