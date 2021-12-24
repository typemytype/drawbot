from Foundation import NSObject, NSMutableAttributedString, NSInsetRect
from AppKit import NSApp, NSColorWell, NSActionCell, NSNotificationCenter, NSFontManager, \
    NSCalibratedRGBColorSpace, NSTableViewFirstColumnOnlyAutoresizingStyle, \
    NSBezierPath, NSFont, NSForegroundColorAttributeName, NSUnderlineColorAttributeName, NSTextAlignmentCenter

from vanilla import *
from vanilla.vanillaBase import VanillaCallbackWrapper
from defconAppKit.windows.baseWindow import BaseWindowController

from drawBot.misc import getDefault, setDefault, getFontDefault, setFontDefault, getColorDefault, setColorDefault

from .codeEditor import _textAttributesForStyle, _hexToNSColor, fallbackBackgroundColor, fallbackHightLightColor, fallbackFont, styleFromDefault, fallbackStyles


class ColorCell(NSActionCell):

    def initWithDoubleClickCallack_(self, callback):
        self = super(ColorCell, self).init()
        self._callback = callback
        return self

    def drawWithFrame_inView_(self, frame, view):
        color = self.objectValue()
        color.set()
        rect = NSInsetRect(frame, 2, 2)
        NSBezierPath.bezierPathWithRect_(rect).fill()

    def hitTestForEvent_inRect_ofView_(self, event, rect, view):
        if hasattr(self, "_callback") and event.clickCount() == 2:
            self._callback(self)
            return True
        return False


class PreviewTokeCell(NSActionCell):

    def drawWithFrame_inView_(self, frame, view):
        frame.origin.x -= 1
        frame.size.width += 2
        frame.origin.y -= 2
        frame.size.height += 2
        textFrame = NSInsetRect(frame, 2, 2)

        text = self.objectValue()
        color = getColorDefault("PyDEBackgroundColor", fallbackBackgroundColor)
        color.set()
        NSBezierPath.bezierPathWithRect_(frame).fill()

        if self.isHighlighted():
            frame.origin.y += 1
            frame.size.height -= 1
            color = getColorDefault("PyDEHightLightColor", fallbackHightLightColor)
            color.set()
            NSBezierPath.bezierPathWithRect_(frame).fill()

        text.drawInRect_(textFrame)


toolTips = {
    "Fallback": "The color used",
    "Text": "",
    "Error": "Color for errors, tracebacks",
    "Punctuation": "Color for puntuaction {[(,.)]}",

    "Keyword": "Color for Python keyword",
    "Keyword.Namespace": "Color for imported modules",

    "Number": "Color for a number",
    "Number.Float": "Color for a float (0.5)",
    "Number.Oct": "Color for a octonal number",
    "Number.Hex": "Color for a hexadecimal number",

    "Name": "Color for all sorts of names",
    "Name.Tag": "Color for tag names",
    "Name.Variable": "Color for varialble names",
    "Name.Attribute": "Color for attributes names",
    "Name.Function": "Color for function names, declaration",
    "Name.Class": "Color for class names, declaration",
    "Name.Constant": "Color for constansts",
    "Name.Namespace": "Color for namespace names (import x form y)",
    "Name.Builtin": "Color for builtin python names (import, max, min, object, ...)",
    "Name.Builtin.Pseudo": "Color for builtin python names (None, self, True, False, ...)",
    "Name.Exception": "Color for exceptions",
    "Name.Decorator": "Color for decorators (@<name>)",


    "Operator": "Color for operators == != <= >=",
    "Operator.Word": "Color for word operators and or not in",

    "Comment": "Color for comments #...",

    "String": "Color for a string",
    "String.Doc": "Color for a doc string",
}


class SyntaxColorPanelDelegate(NSObject):

    def __new__(cls, *args, **kwargs):
        return cls.alloc().init()

    def __init__(self, callback):
        self._callback = callback

    def changeColor_(self, sender):
        self._callback(sender)


class SyntaxColorListDelegate(NSObject):

    def tableView_toolTipForCell_rect_tableColumn_row_mouseLocation_(self, tableView, cell, rect, column, row, location):
        value = None
        if column.identifier() == "tokenString":
            value = cell.objectValue().string()
        return toolTips.get(value, ""), rect


class SyntaxPopupColorPanel(NSObject):

    def __new__(cls, *args, **kwargs):
        return cls.alloc().init()

    def __init__(self, callback, color, alpha=True):
        self._callback = callback
        self.colorWell = NSColorWell.alloc().init()
        self.colorWell.setColor_(color)
        self.colorWell.setTarget_(self)
        self.colorWell.setAction_("changeColor:")
        self.colorWell.performClick_(self)

    def changeColor_(self, sender):
        self._callback(sender)


class ColorItem(NSObject):

    def __new__(cls, *args, **kwargs):
        return cls.alloc().init()

    def __init__(self, style):
        self._style = style

    def tokenString(self):
        font = NSFont.fontWithName_size_(fallbackFont.fontName(), 10)
        attr = _textAttributesForStyle(self._style, font)
        attr[NSForegroundColorAttributeName] = self.color()
        if NSUnderlineColorAttributeName in attr:
            attr[NSUnderlineColorAttributeName] = self.color()
        txt = self.token()
        if txt == "Token":
            txt = "Fallback"
        else:
            txt = txt.replace("Token.", "")
        return NSMutableAttributedString.alloc().initWithString_attributes_(txt, attr)

    def token(self):
        return self._style["token"]

    def tokenValue(self):
        value = [self.hexColor()]
        if self.bold():
            value.append("bold")
        if self.italic():
            value.append("italic")
        if self.underline():
            value.append("underline")
        return " ".join(value)

    def color(self):
        return _hexToNSColor(self.hexColor())

    def hexColor(self):
        return self._style["color"]

    def setColor_(self, color):
        color = color.colorUsingColorSpaceName_(NSCalibratedRGBColorSpace)
        r = int(color.redComponent() * 255)
        g = int(color.greenComponent() * 255)
        b = int(color.blueComponent() * 255)
        self._style["color"] = "%02X%02X%02X" % (r, g, b)

    def bold(self):
        return self._style.get("bold", False)

    def setBold_(self, value):
        self._style["bold"] = value

    def italic(self):
        return self._style.get("italic", False)

    def setItalic_(self, value):
        self._style["italic"] = value
        self.setColor_(self.color())

    def underline(self):
        return self._style.get("underline", False)

    def setUnderline_(self, value):
        self._style["underline"] = value


class SyntaxColors(Group):

    def __init__(self, posSize):
        self._initializing = True
        super(SyntaxColors, self).__init__(posSize)

        middle = 100
        gutter = 5

        x = 10
        y = 10
        self.fontText = TextBox((x, y, middle, 22), "Font:", alignment="right")
        self.font = EditText((x + middle + gutter, y, -100, 22), readOnly=True)
        self.font.getNSTextField().setAlignment_(NSTextAlignmentCenter)
        self.selectFont = Button((-90, y, -10, 22), "Select...", callback=self.selectFontCallback)
        y += 30
        self.backgroundColorText = TextBox((x, y, middle, 22), "Background:", alignment="right")
        self.backgroundColor = ColorWell((x + middle + gutter, y - 2, 50, 25), callback=self.setToDefaults)

        x = -255
        self.hightLightColorText = TextBox((x, y, middle, 22), "Text Selection:", alignment="right")
        self.hightLightColor = ColorWell((x + middle + gutter, y - 2, 50, 25), callback=self.setToDefaults)
        y += 30

        columnDescriptions = [
            dict(title="Element", key="tokenString", width=170, cell=PreviewTokeCell.alloc().init()),
            dict(title="Color", key="color", width=100, cell=ColorCell.alloc().initWithDoubleClickCallack_(self.colorDoubleClickCallback), editable=True),
            dict(title="", key="bold", width=50, cell=CheckBoxListCell("Bold")),
            dict(title="", key="italic", width=50, cell=CheckBoxListCell("Italic")),
            dict(title="", key="underline", width=90, cell=CheckBoxListCell("Underline")),
        ]

        self.tokenList = List((10, y, -10, -10), [],
                              columnDescriptions=columnDescriptions,
                              editCallback=self.editCallback,
                              allowsEmptySelection=True,
                              allowsMultipleSelection=True,
                              drawVerticalLines=False
                              )
        self.tokenList.getNSTableView().setColumnAutoresizingStyle_(NSTableViewFirstColumnOnlyAutoresizingStyle)
        self.tokenList.getNSTableView().setUsesAlternatingRowBackgroundColors_(False)
        self._delegate = SyntaxColorListDelegate.alloc().init()
        self.tokenList.getNSTableView().setDelegate_(self._delegate)

        self._initializing = False

    # list

    def getSelectedItems(self):
        sel = self.tokenList.getSelection()
        return [self.tokenList[i] for i in sel]

    def editCallback(self, sender):
        self.setToDefaults()

    # color

    def setStyleColor_(self, sender):
        items = self.getSelectedItems()
        for item in items:
            item.setColor_(sender.color())

    def colorDoubleClickCallback(self, sender):
        items = self.getSelectedItems()
        if not items:
            return
        item = items[0]
        self._syntaxPopupColorPanel = SyntaxPopupColorPanel(self.setStyleColor_, item.color(), alpha=False)

    # font

    def _setFont(self, font):
        self.font.getNSTextField().setFont_(NSFont.fontWithName_size_(font.fontName(), 10))
        size = font.pointSize()
        if size == int(size):
            size = int(size)
        s = u"%s %spt" % (font.displayName(), size)
        self.font.set(s)

    def _selectFontCallback(self, sender):
        oldFont = getFontDefault("PyDEFont", fallbackFont)
        newFont = sender.convertFont_(oldFont)
        if oldFont != newFont:
            self._setFont(newFont)
            setFontDefault("PyDEFont", newFont)
            self.preferencesChanged()

    def selectFontCallback(self, sender):
        fm = NSFontManager.sharedFontManager()
        fm.setSelectedFont_isMultiple_(getFontDefault("PyDEFont", fallbackFont), False)
        fm.orderFrontFontPanel_(sender)
        fp = fm.fontPanel_(False)

        self._fontCallbackWrapper = VanillaCallbackWrapper(self._selectFontCallback)
        fm.setTarget_(self._fontCallbackWrapper)
        fm.setAction_("action:")

    # defaults

    def getFromDefaults(self):
        self._initializing = True
        self._setFont(getFontDefault("PyDEFont", fallbackFont))

        styles = styleFromDefault()
        items = []

        for token, value in fallbackStyles:
            data = dict(token=str(token))
            style = styles.style_for_token(token)
            data.update(style)
            item = ColorItem(data)
            items.append(item)
        self.tokenList.set(items)

        self.backgroundColor.set(getColorDefault("PyDEBackgroundColor", fallbackBackgroundColor))
        self.hightLightColor.set(getColorDefault("PyDEHightLightColor", fallbackHightLightColor))
        self._initializing = False

    def setToDefaults(self, sender=None):
        if self._initializing:
            return
        setColorDefault("PyDEBackgroundColor", self.backgroundColor.get())
        setColorDefault("PyDEHightLightColor", self.hightLightColor.get())

        tokens = dict()
        for item in self.tokenList:
            tokens[item.token()] = item.tokenValue()
        setDefault("PyDETokenColors", tokens)

        self.tokenList.getNSTableView().setNeedsDisplay_(True)
        self.preferencesChanged()

    def preferencesChanged(self, sender=None):
        nc = NSNotificationCenter.defaultCenter()
        nc.postNotificationName_object_userInfo_("drawBotUserDefaultChanged", None, None)


class PreferencesController(BaseWindowController):

    def __init__(self):
        self.w = Window((500, 430), miniaturizable=False, minSize=(500, 430))

        y = -190
        self.w.syntaxColors = SyntaxColors((0, 0, -0, y))

        self.w.hl1 = HorizontalLine((10, y, -10, 1))
        y += 10
        self.w.clearOutPut = CheckBox((10, y, -10, 22), "Clear text output before running script", callback=self.setToDefaults)
        y += 30
        self.w.liveOutPut = CheckBox((10, y, -10, 22), "Live update output", callback=self.setToDefaults)
        y += 30
        self.w.shouldOpenUntitledFile = CheckBox((10, y, -10, 22), "Should Open Untitled File", callback=self.setToDefaults)
        y += 30
        self.w.showToolbar = CheckBox((10, y, -10, 22), "Add Toolbar", callback=self.setToDefaults)
        y += 30
        self.w.animateIcon = CheckBox((10, y, -10, 22), "Animate Icon", callback=self.anitmateIconCallback)
        y += 30
        self.w.checkForUpdates = CheckBox((10, y, 230, 22), "Check For Updates at Startup", callback=self.setToDefaults)
        self.w.checkNow = Button((230, y, 100, 22), "Check Now", callback=self.checkNowCallback, sizeStyle="small")
        self.setUpBaseWindowBehavior()
        self.getFromDefaults()
        self.w.open()

    def getFromDefaults(self):
        self.w.clearOutPut.set(getDefault("DrawBotClearOutput", True))
        self.w.liveOutPut.set(getDefault("DrawButLiveUpdateStdoutStderr", False))
        self.w.animateIcon.set(getDefault("DrawBotAnimateIcon", True))
        self.w.checkForUpdates.set(getDefault("DrawBotCheckForUpdatesAtStartup", True))
        self.w.shouldOpenUntitledFile.set(getDefault("shouldOpenUntitledFile", True))
        self.w.showToolbar.set(getDefault("DrawBotAddToolbar", True))
        self.w.syntaxColors.getFromDefaults()

    def setToDefaults(self, sender=None):
        setDefault("DrawBotClearOutput", self.w.clearOutPut.get())
        setDefault("DrawButLiveUpdateStdoutStderr", self.w.liveOutPut.get())
        setDefault("DrawBotAnimateIcon", self.w.animateIcon.get())
        setDefault("DrawBotCheckForUpdatesAtStartup", self.w.checkForUpdates.get())
        setDefault("shouldOpenUntitledFile", self.w.shouldOpenUntitledFile.get())
        setDefault("DrawBotAddToolbar", self.w.showToolbar.get())

    def anitmateIconCallback(self, sender):
        self.setToDefaults()
        NSApp().delegate().sheduleIconTimer()

    def checkNowCallback(self, sender):
        from drawBot.updater import Updater
        oldValue = getDefault("DrawBotCheckForUpdatesAtStartup", True)
        setDefault("DrawBotCheckForUpdatesAtStartup", True)
        updater = Updater(self.w)
        if updater.currentVersionErrors:
            self.showMessage("Cannot retrieve the version number from the DrawBot repository.", "\n".join(updater.currentVersionErrors))
        elif not updater.needsUpdate:
            self.showMessage("You have the latest version!", "DrawBot %s is currently the newest version" % updater.__version__)
        setDefault("DrawBotCheckForUpdatesAtStartup", oldValue)

    def show(self):
        self.w.show()


if __name__ == "__main__":
    from vanilla.test.testTools import executeVanillaTest
    executeVanillaTest(PreferencesController)
