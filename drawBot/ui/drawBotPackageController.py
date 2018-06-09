import os

from defconAppKit.windows.baseWindow import BaseWindowController

import vanilla

from drawBot.drawBotPackage import DrawBotPackage


class DrawBotPackageController(BaseWindowController):

    packageInfo = [
        "name",
        "version",
        "developer",
        "developerURL",
        "requiresVersion",
        "mainScript",
    ]

    def __init__(self):
        self.bundle = DrawBotPackage()

        self.w = vanilla.Window((350, 320), "Package builder")

        y = 10
        m = 120
        for attr in self.packageInfo:
            text = vanilla.TextBox((10, y, m - 15, 22), "%s:" % attr, alignment="right")
            edit = vanilla.EditText((m, y, -10, 22), placeholder=getattr(self.bundle.info, attr))

            setattr(self.w, "%s_text" % attr, text)
            setattr(self.w, "%s_edit" % attr, edit)
            y += 30

        self.w.note = vanilla.TextBox((m, y, -10, 22), "Everything is optional.", sizeStyle="mini")
        y += 30
        self.w.h1 = vanilla.HorizontalLine((0, y, 0, 1))
        y += 10
        self.w.scriptRoot_text = vanilla.TextBox((10, y, m - 15, 22), "Script Root:", alignment="right")
        self.w.scriptRoot = vanilla.PathControl((m, y - 2, -10, 22), None, pathStyle="popUp", callback=self.scriptRootCallback)
        y += 25
        self.w.scriptRoot_note = vanilla.TextBox((m, y, -10, 22), "A folder containing all required python files.", sizeStyle="mini")

        self.w.buildButton = vanilla.Button((-120, -30, -10, 22), "Build", callback=self.buildCallback)
        self.w.open()

    def scriptRootCallback(self, sender):
        url = sender.get()
        if url and not os.path.isdir(url):
            sender.set(None)
            self.showMessage("Package error.", "The script root must be a folder.")

    def buildCallback(self, sender):
        for attr in self.packageInfo:
            control = getattr(self.w, "%s_edit" % attr)
            value = str(control.get())
            if value:
                setattr(self.bundle.info, attr, value)
        root = self.w.scriptRoot.get()
        if root is None:
            self.showMessage("Package error.", "A scripting root must be provided.")
            return

        def saveBundle(path):
            if path:
                succes, report = self.bundle.buildPackage(path, root)
                if not succes:
                    self.showMessage("Package error.", report)

        self.showPutFile(["drawbot"], saveBundle)
