import os
import select
import subprocess
import sys
import threading
import AppKit
from PyObjCTools.AppHelper import callAfter
from vanilla import *
from vanilla.dialogs import message
from drawBot.ui.codeEditor import OutPutEditor as OutputEditor


class MyActionButton(ActionButton):

    def __init__(self, posSize, items, *args, **kwargs):
        super().__init__(posSize, items, *args, **kwargs)
        self._nsObject.setAutoenablesItems_(False)
        self.menuItemIndices = {item["name"]: index + 1 for index, item in enumerate(items)}
        separatorIndices = [index + 1 for index, item in enumerate(items) if not item["title"]]
        menu = self._nsObject.menu()
        for index in separatorIndices:
            item = AppKit.NSMenuItem.separatorItem()
            menu.removeItemAtIndex_(index)
            menu.insertItem_atIndex_(item, index)

    def enableItem(self, name, onoff):
        item = self._nsObject.itemAtIndex_(self.menuItemIndices[name])
        item.setEnabled_(onoff)


class PipInstallerController:

    def __init__(self, targetPath):
        self.targetPath = targetPath
        self._isRunning = False

        y = 15
        self.w = Window((640, 300), "Install External Python Packages", 
                minSize=(640, 300), autosaveName="PipInstaller")
        items = [
            dict(name="search", title="Search PyPI", callback=self.pipSearchCallback),
            dict(name="install", title="Install / Upgrade", callback=self.pipInstallCallback),
            dict(name="uninstall", title="Uninstall", callback=self.pipUninstallCallback),
            dict(name="showInfo", title="Show Package Info", callback=self.pipShowCallback),
            dict(name="_separator_", title=""),
            dict(name="list", title="List Installed Packages", callback=self.pipListCallback),
            dict(name="showInstallFolder", title="Show Install Folder", callback=self.showInstallFolderCallback),
            dict(name="showPipVersion", title="Show Pip Version", callback=self.pipVersionCallback),
        ]
        self.w.actionButton = MyActionButton((15, y, 40, 25), items)
        self.w.textEntry = EditText((70, y, -55, 25), placeholder="Enter a package name",
                callback=self.textEntryChanged)
        self.w.progressSpinner = ProgressSpinner((-40, y, 25, 25))
        y += 35

        self.w.outputField = OutputEditor((0, y, -0, -20), readOnly=True)
        self.w.resultcodeField = TextBox((10, -18, 200, 0), "", sizeStyle="small")

        self.textEntryChanged(None)  # set menu items to initial state
        self.w.open()

        self.w.bind("should close", self.windowShouldClose)
        self.stdoutCallback("Welcome to pip! Pip installs Python Packages from the PyPI database.\n")
        self.stdoutCallback("Enter a package name in the text field, then choose an action from the “gear” button.\n")

    def show(self):
        if self.w._window is None:
            # We have been closed, let's start over
            self.__init__(self.targetPath)
        else:
            self.w.show()

    def windowShouldClose(self, window):
        if self.isRunning:
            message("Window can’t be closed", "The ‘pip’ process is still running.",
                    parentWindow=self.w)
            return False
        return True

    @property
    def isRunning(self):
        return self._isRunning

    @isRunning.setter
    def isRunning(self, onoff):
        self._isRunning = onoff
        self.enableActionMenuItems(not onoff)
        if onoff:
            self.w.progressSpinner.start()
        else:
            self.w.progressSpinner.stop()
        self.w.actionButton.enableItem("showInstallFolder", os.path.exists(self.targetPath))

    @property
    def enteredText(self):
        return self.w.textEntry.get().strip()

    def enableActionMenuItems(self, onoff):
        for menuName in ["list", "showPipVersion"]:
            self.w.actionButton.enableItem(menuName, onoff)
        if not self.enteredText:
            onoff = False
        for menuName in ["search", "install", "showInfo", "uninstall"]:
            self.w.actionButton.enableItem(menuName, onoff)

    def textEntryChanged(self, sender):
        if self.isRunning:
            return
        self.enableActionMenuItems(not self.isRunning)

    def pipSearchCallback(self, sender):
        self.callPip(["search", self.enteredText])

    def pipInstallCallback(self, sender):
        if not os.path.exists(self.targetPath):
            os.makedirs(self.targetPath)
            if self.targetPath not in sys.path:
                sys.path.append(self.targetPath)
        self.callPip(["install", "--upgrade", "--target", self.targetPath, self.enteredText])

    def pipShowCallback(self, sender):
        self.callPip(["show", self.enteredText])

    def pipListCallback(self, sender):
        self.callPip(["list", self.enteredText])

    def pipUninstallCallback(self, sender):
        outputLines = []
        def collectOutput(data):
            outputLines.append(data)
        def doneShowCallback(resultcode):
            if resultcode != 0:
                self.stderrCallback("".join(outputLines))
                self.isRunning = False
                return
            tag = "Location:"
            locationLines = [line for line in outputLines if line.startswith(tag)]
            if not locationLines:
                self.stderrCallback("".join(outputLines))
                self.isRunning = False
                return
            locationLine = locationLines[0][len(tag):].strip()
            if locationLine != self.targetPath:
                self.stderrCallback(f"Can't uninstall: {self.enteredText} is not installed in {self.targetPath}\n")
                self.isRunning = False
            else:
                self.callPip(["uninstall", self.enteredText, "-y"])
        self.w.outputField.clear()
        self.isRunning = True
        self.setResultCode("--")
        callPip(["show", self.enteredText], collectOutput, collectOutput, doneShowCallback)

    def pipVersionCallback(self, sender):
        self.callPip(["--version"])

    def showInstallFolderCallback(self, sender):
        AppKit.NSWorkspace.sharedWorkspace().selectFile_inFileViewerRootedAtPath_(None, self.targetPath)

    def callPip(self, arguments):
        self.w.outputField.clear()
        self.isRunning = True
        self.setResultCode("--")
        callPip(arguments, self.stdoutCallback, self.stderrCallback, self.resultCallback)

    def stdoutCallback(self, data):
        self.w.outputField.append(data)
        self.w.outputField.scrollToEnd()

    def stderrCallback(self, data):
        self.w.outputField.append(data, isError=True)
        self.w.outputField.scrollToEnd()

    def resultCallback(self, resultcode):
        self.setResultCode(resultcode)
        self.isRunning = False

    def setResultCode(self, resultcode):
        self.w.resultcodeField.set(f"pip result code: {resultcode}")


def callPip(arguments, stdoutCallback, stderrCallback, resultCallback):
    arguments = [sys.executable, '-m', "pip", "--disable-pip-version-check", "--isolated"] + arguments
    env = dict(PYTHONPATH=":".join(sys.path), PATH="/usr/bin")
    callExternalProcess("pip", arguments, env, stdoutCallback, stderrCallback, resultCallback)


def _testTimeout():
    arguments = [sys.executable, '-c', "import time; print('Hiiiiiii'); time.sleep(3)"]
    env = dict(PYTHONPATH=":".join(sys.path), PATH="/usr/bin")
    callExternalProcess("pip", arguments, env, print, print, print, timeout=1)


def callExternalProcess(name, arguments, env, stdoutCallback, stderrCallback, resultCallback, timeout=15):
    def worker():
        process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=env, encoding="utf-8")
        readers = [process.stdout, process.stderr]
        while readers:
            readyReaders, _, _ = select.select(readers, [], [], timeout)
            if not readyReaders:
                process.kill()
                callAfter(stderrCallback, f"The {name} process timed out (in select.select())")
                callAfter(resultCallback, -1)
                return
            for reader in readyReaders:
                data = reader.readline()
                if not data:
                    readers.remove(reader)
                    continue
                if reader is process.stderr:
                    callAfter(stderrCallback, data)
                else:
                    callAfter(stdoutCallback, data)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            callAfter(stderrCallback, f"The {name} process timed out (in process.wait())")
            callAfter(resultCallback, -1)
            return
        callAfter(resultCallback, process.returncode)
    thread = threading.Thread(target=worker)
    thread.start()


if __name__ == "__main__":
    # _testTimeout()
    appSupportPath = AppKit.NSSearchPathForDirectoriesInDomains(
            AppKit.NSApplicationSupportDirectory,
            AppKit.NSUserDomainMask, True)[0]
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    dbSitePath = os.path.join(appSupportPath, f"DrawBot/Python{version}")
    PipInstallerController(dbSitePath)
