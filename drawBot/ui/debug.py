from Foundation import NSLog
from AppKit import NSPanel

import sys

from vanilla import *

from .codeEditor import OutPutEditor


class ShowHideNSPanel(NSPanel):

    def close(self):
        self.orderOut_(None)


class ShowHideFloatingWindow(FloatingWindow):

    nsWindowClass = ShowHideNSPanel


class DebugWindowController(object):

    """
    Debugger catching all sys.stdout and sys.sterr outside a script.
    """

    def __init__(self):
        self.w = ShowHideFloatingWindow((300, 500), "Debugger",
                                    minSize=(200, 300),
                                    autosaveName="DrawBotDebugWindow",
                                    initiallyVisible=False)

        self.w.debugText = OutPutEditor((0, 0, -0, -0), readOnly=True)

        self._savedStdout = sys.stdout
        self._savedStderr = sys.stderr

        sys.stdout = self
        sys.stderr = self

        self.w.open()

    def showHide(self):
        if self.w.isVisible():
            self.w.hide()
        else:
            self.show()

    def show(self):
        self.w.show()
        self.w.select()

    def clear(self, sender=None):
        """
        Clear all text in the output window.
        """
        self.w.debugText.clear()

    def write(self, inputText):
        """
        Write text in the output window.
        Duplicate the text also in the default logging system
        so it will appear in the console.app.
        """
        NSLog(inputText)
        self.w.debugText.append(inputText)
        self.w.debugText.scrollToEnd()

    def flush(self):
        pass
