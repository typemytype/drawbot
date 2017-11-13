from __future__ import absolute_import, print_function

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen
import subprocess
import plistlib
import AppKit

from distutils.version import StrictVersion

import vanilla
from defconAppKit.windows.progressWindow import ProgressWindow

from drawBot import __version__
from .misc import DrawBotError, getDefault

from fontTools.misc.py23 import unichr, PY2


def getCurrentVersion():
    """
    Return the newest version number from github.
    """
    if not getDefault("checkForUpdatesAtStartup", True):
        return ""
    path = "https://raw.github.com/typemytype/drawbot/master/drawBot/drawBotSettings.py"
    try:
        response = urlopen(path, timeout=5)
        code = response.read()
        response.close()
        exec(code)
    except:
        __version__ = ""
    return __version__


def downloadCurrentVersion():
    """
    Download the current version (dmg) and mount it
    """
    if PY2:
        path = "http://static.typemytype.com/drawBot/DrawBot.dmg"
    else:
        path = "http://static.typemytype.com/drawBot/DrawBotPy3.dmg"
    try:
        # download and mount
        cmds = ["hdiutil", "attach", "-plist", path]
        popen = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = popen.communicate()
        if popen.returncode != 0:
            raise DrawBotError("Mounting failed")
        output = plistlib.readPlistFromString(out)
        dmgPath = None
        for item in output["system-entities"]:
            if "mount-point" in item:
                dmgPath = item["mount-point"]
                break
        AppKit.NSWorkspace.sharedWorkspace().openFile_(dmgPath)
    except:
        print("Something went wrong while downloading %s" % path)


class Updater(object):
    """
    Small controller poping up if a update is found.
    """
    def __init__(self, parentWindow=None):
        self.needsUpdate = False
        self.__version__ = __version__
        if not getDefault("DrawBotCheckForUpdatesAtStartup", True):
            return
        self.currentVersion = getCurrentVersion()
        self.needsUpdate = StrictVersion(__version__) < StrictVersion(self.currentVersion)
        if not self.needsUpdate:
            return
        if parentWindow:
            self.w = vanilla.Sheet((450, 130), parentWindow=parentWindow)
        else:
            self.w = vanilla.Window((450, 130))

        self.w.appIcon = vanilla.ImageView((25, 15, 65, 65))
        self.w.appIcon.setImage(imageObject=AppKit.NSApp().applicationIconImage())

        title = "There is a new version of DrawBot!"
        txt = AppKit.NSAttributedString.alloc().initWithString_attributes_(title, {AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(0)})
        self.w.introBold = vanilla.TextBox((100, 15, -15, 20), txt)

        self.w.intro = vanilla.TextBox((100, 45, -15, 200), "DrawBot %s is out now (you have %s).\nWould you like to download it now?" % (self.currentVersion, __version__), sizeStyle="small")

        self.w.cancelButton = vanilla.Button((-270, -30, 60, 20), "Cancel", callback=self.cancelCallback, sizeStyle="small")
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(unichr(27), [])

        self.w.openInBrowser = vanilla.Button((-200, -30, 120, 20), "Show In Browser", callback=self.openInBrowserCallback, sizeStyle="small")
        self.w.okButton = vanilla.Button((-70, -30, 55, 20), "OK", callback=self.okCallback, sizeStyle="small")
        self.w.setDefaultButton(self.w.okButton)

        self.w.open()

    def cancelCallback(self, sender):
        self.w.close()

    def openInBrowserCallback(self, sender):
        url = "http://www.drawbot.com/content/download.html"
        url = AppKit.NSURL.URLWithString_(url)
        AppKit.NSWorkspace.sharedWorkspace().openURL_(url)
        self.w.close()

    def okCallback(self, sender):
        self.w.close()
        progress = ProgressWindow("Downloading DrawBot %s" % self.currentVersion)
        downloadCurrentVersion()
        progress.close()
