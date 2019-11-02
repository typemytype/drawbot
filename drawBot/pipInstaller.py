import os
import re
import select
import shlex
import subprocess
import sys
import threading
import AppKit
from PyObjCTools.AppHelper import callAfter
from vanilla import *
from vanilla.dialogs import message
from drawBot.ui.codeEditor import OutPutEditor as OutputEditor


welcomeText = """\
Welcome to pip! Pip installs Python Packages from the PyPI database.

Enter one or more package names in the text field, choose an action from \
the popup button on the left, then click “Go!” or hit return or enter.
"""

class PipInstallerController:

    def __init__(self, targetPath):
        self.targetPath = targetPath
        self._isRunning = False

        self.w = Window((640, 300), minSize=(640, 300), autosaveName="PipInstaller")
        # Fake empty toolbar, so we get a Safari-like appearance
        self.w.getNSWindow().setTitlebarAppearsTransparent_(True)
        self.w.getNSWindow().setTitleVisibility_(True)
        self.w.getNSWindow().setStyleMask_(self.w.getNSWindow().styleMask() | AppKit.NSWindowStyleMaskFullSizeContentView)
        self.w.getNSWindow().setToolbar_(AppKit.NSToolbar.alloc().initWithIdentifier_("PipEmptyToolbar"))

        y = 7
        items = ["Search PyPI", "Install / Upgrade", "Uninstall", "Show Package Info"]
        self.pipCommandNames = [f"pip{re.sub(r'[ /]', '', item)}Command" for item in items]
        self.w.pipCommandsButton = PopUpButton((80, y+1, 140, 22), items)
        self.w.pipCommandsButton.getNSPopUpButton().setBezelStyle_(AppKit.NSBezelStyleTexturedRounded)        
        self.w.textEntry = EditText((234, y+2, -152, 21), placeholder="Enter one or more package names",
                callback=self.textEntryCallback)
        self.w.goButton = Button((-142, y+2, 50, 21), "Go!", callback=self.goButtonCallback)
        self.w.goButton.enable(False)
        self.w.setDefaultButton(self.w.goButton)
        self.w.progressSpinner = ProgressSpinner((-82, y+3, 18, 18))

        items = [
            dict(name="list", title="List Installed Packages", callback=self.pipListCallback),
            dict(name="showPipVersion", title="Show Pip Version", callback=self.pipVersionCallback),
            "----",
            dict(name="revealInstallFolder", title="Reveal Install Folder in Finder", callback=self.revealInstallFolderCallback),
        ]
        self.w.extraActionButton = ActionButton((-50, y, 35, 25), items)
        y += 30

        self.w.outputField = OutputEditor((0, y, -0, -20), readOnly=True)
        self.w.resultCodeField = TextBox((10, -18, 200, 0), "", sizeStyle="small")

        self.w.open()

        self.w.bind("should close", self.windowShouldClose)
        self.stdoutWrite(welcomeText)

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
        if onoff:
            self.w.progressSpinner.start()
        else:
            self.w.progressSpinner.stop()
        self.w.goButton.enable(not onoff)

    def getUserArguments(self):
        return shlex.split(self.w.textEntry.get())

    def goButtonCallback(self, sender):
        commandName = self.pipCommandNames[self.w.pipCommandsButton.get()]
        getattr(self, commandName)(self.getUserArguments())

    def textEntryCallback(self, sender):
        if self.isRunning:
            return
        self.w.goButton.enable(bool(self.getUserArguments()))

    def pipSearchPyPICommand(self, userArguments):
        self.callPip(["search"] + userArguments)

    def pipInstallUpgradeCommand(self, userArguments):
        if not os.path.exists(self.targetPath):
            os.makedirs(self.targetPath)
            if self.targetPath not in sys.path:
                sys.path.append(self.targetPath)
        self.callPip(["install", "--upgrade", "--target", self.targetPath] + userArguments)

    def pipShowPackageInfoCommand(self, userArguments):
        self.callPip(["show"] + userArguments)

    def pipListCallback(self, sender):
        self.callPip(["list"])

    def pipUninstallCommand(self, userArguments):
        packageNames = [arg.lower() for arg in userArguments if not arg.startswith("-")]
        extraArguments = [arg for arg in userArguments if arg.startswith("-")]
        outputLines = []
        def collectOutput(data):
            outputLines.append(data)
        def doneShowCallback(resultCode):
            if resultCode != 0:
                self.stderrWrite("".join(outputLines))
                self.setResultCode(resultCode)
                self.isRunning = False
                return
            packages = {}
            nameTag = "Name:"
            locationTag = "Location:"
            for line in outputLines:
                if line.startswith(nameTag):
                    name = line[len(nameTag):].strip()
                elif line.startswith(locationTag):
                    location = line[len(locationTag):].strip()
                    assert name is not None
                    packages[name.lower()] = location
                    name = None
            packageNamesNotFound = {name for name in packageNames if name not in packages}
            packageNamesBad = [name for name in packageNames if name in packages and packages[name] != self.targetPath]
            packageNamesGood = [name for name in packageNames if name in packages and packages[name] == self.targetPath]
            for name in packageNamesNotFound:
                self.stderrWrite(f"Skipping {name} as it is not installed\n")
            for name in packageNamesBad:
                self.stderrWrite(f"Skipping {name} as it is not installed in {self.targetPath}\n")
            if packageNamesGood:
                self.callPip(["uninstall", "-y"] + extraArguments + packageNamesGood, clearOutput=False)
            else:
                self.isRunning = False
        self.w.outputField.clear()
        self.isRunning = True
        self.setResultCode("--")
        callPip(["show"] + packageNames, collectOutput, collectOutput, doneShowCallback)

    def pipVersionCallback(self, sender):
        self.callPip(["--version"])

    def revealInstallFolderCallback(self, sender):
        if not os.path.exists(self.targetPath):
            message("The install folder does not yet exists.", "Try again after installing a package.", parentWindow=self.w)
        else:
            AppKit.NSWorkspace.sharedWorkspace().selectFile_inFileViewerRootedAtPath_(None, self.targetPath)

    def callPip(self, arguments, clearOutput=True):
        if clearOutput:
            self.w.outputField.clear()
        self.isRunning = True
        self.setResultCode("--")
        callPip(arguments, self.stdoutWrite, self.stderrWrite, self.resultCallback)

    def stdoutWrite(self, data):
        self.w.outputField.append(data)
        self.w.outputField.scrollToEnd()

    def stderrWrite(self, data):
        self.w.outputField.append(data, isError=True)
        self.w.outputField.scrollToEnd()

    def resultCallback(self, resultCode):
        self.setResultCode(resultCode)
        self.isRunning = False
        if resultCode == 23:  # special pip error code
            self.stdoutWrite("No results.\n")

    def setResultCode(self, resultCode):
        self.w.resultCodeField.set(f"pip result code: {resultCode}")


def callPip(arguments, stdoutCallback, stderrCallback, resultCallback):
    arguments = [sys.executable, '-m', "pip", "--disable-pip-version-check", "--isolated"] + arguments
    env = dict(PYTHONPATH=":".join(sys.path), PYTHONHOME=sys.prefix, PATH="/usr/bin")
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
