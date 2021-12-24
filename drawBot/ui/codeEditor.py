import AppKit
from objc import super

from keyword import kwlist
import re
import sys

from pygments.lexers import Python3Lexer, get_lexer_by_name
from pygments.token import *
from pygments.style import Style
from pygments.styles.default import DefaultStyle

try:
    import jedi
    hasJedi = True
except Exception:
    hasJedi = False

from vanilla import *
from vanilla.py23 import python_method

from .lineNumberRulerView import LineNumberNSRulerView
from drawBot.misc import getDefault, getFontDefault, getColorDefault, DrawBotError, nsStringLength
from drawBot.drawBotDrawingTools import _drawBotDrawingTool


MAXFLOAT = sys.float_info.max

variableChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"

fallbackTextColor = AppKit.NSColor.blackColor()
fallbackBackgroundColor = AppKit.NSColor.whiteColor()
fallbackHightLightColor = AppKit.NSColor.selectedTextBackgroundColor()

fallbackFont = AppKit.NSFont.fontWithName_size_("Menlo", 10)
if not fallbackFont:
    fallbackFont = AppKit.NSFont.fontWithName_size_("Monaco", 10)

basicLineHeightMultiple = 1.2
basicParagraph = AppKit.NSMutableParagraphStyle.alloc().init()
basicParagraph.setDefaultTabInterval_(28.0)
basicParagraph.setTabStops_(AppKit.NSArray.array())
basicParagraph.setLineHeightMultiple_(basicLineHeightMultiple)

fallbackTypeAttributes = {
    AppKit.NSFontAttributeName: fallbackFont,
    AppKit.NSLigatureAttributeName: 0,
    AppKit.NSParagraphStyleAttributeName: basicParagraph
}

fallbackTracebackAttributes = dict(fallbackTypeAttributes)
fallbackTracebackAttributes[AppKit.NSForegroundColorAttributeName] = AppKit.NSColor.redColor()

fallbackStyles = [
    (Token,               '#000000'),

    (Generic.Heading,     '#813E94'),
    (Generic.Subheading,  '#1A8BAD'),
    (Generic.Strong,      '#6F00FF'),
    (Generic.Emph,        '#FF00B3'),

    (Text,                ''),
    (Error,               '#FF0000'),
    (Punctuation,         '#6E6E6E'),

    (Keyword,             '#4978FC'),
    (Keyword.Namespace,   '#1950FD'),

    (Number,              '#CC5858'),
    (Number.Float,        ''),
    (Number.Oct,          ''),
    (Number.Hex,          ''),

    (Name,                ''),
    (Name.Tag,            '#fb660a'),
    (Name.Variable,       '#fb660a'),
    (Name.Attribute,      '#ff0086'),
    (Name.Function,       '#ff0086'),
    (Name.Class,          '#ff0086'),
    (Name.Constant,       '#0086d2'),
    (Name.Namespace,      ''),
    (Name.Builtin,        '#31A73E'),
    (Name.Builtin.Pseudo, '#FF8700'),
    (Name.Exception,      '#FF1400'),
    (Name.Decorator,      ''),

    (Operator,            '#6D37C9'),
    (Operator.Word,       '#6D37C9'),

    (Comment,             '#A3A3A3'),

    (String,              '#FC00E7'),
    (String.Doc,          '#FC00E7'),
]

fallbackStyleDict = {}
for key, value in fallbackStyles:
    fallbackStyleDict[str(key)] = value


def styleFromDefault():
    styles = dict()
    tokens = getDefault("PyDETokenColors", fallbackStyleDict)
    for key, value in tokens.items():
        token = string_to_tokentype(key)
        if value and not value.startswith("#"):
            value = "#%s" % value
        styles[token] = value
    style = type('DrawBotStyle', (Style,), dict(styles=styles))
    style.background_color = _NSColorToHexString(getColorDefault("PyDEBackgroundColor", fallbackBackgroundColor))
    style.highlight_color = _NSColorToHexString(getColorDefault("PyDEHightLightColor", fallbackHightLightColor))
    return style


def outputTextAttributesForStyles(styles=None, isError=False):
    if styles is None:
        styles = styleFromDefault()
    if isError:
        style = styles.style_for_token(Error)
    else:
        style = styles.style_for_token(Token)
    attr = _textAttributesForStyle(style)
    for key in (AppKit.NSForegroundColorAttributeName, AppKit.NSUnderlineColorAttributeName):
        if key in attr:
            attr[key] = _hexToNSColor(attr[key])
    return attr


class _JumpToLineSheet(object):

    def __init__(self, callback, parentWindow):
        self._callback = callback
        self.w = Sheet((210, 80), parentWindow=parentWindow)

        self.w.text = TextBox((15, 15, 200, 22), "Jump to line number:")
        self.w.lineNumber = EditText((-55, 17, -15, 18), sizeStyle="small")

        self.w.cancelButton = Button((-170, -30, -80, 20), "Cancel", callback=self.cancelCallback, sizeStyle="small")
        self.w.cancelButton.bind(".", ["command"])
        self.w.cancelButton.bind(chr(27), [])

        self.w.okButton = Button((-70, -30, -10, 20), "OK", callback=self.okCallback, sizeStyle="small")
        self.w.setDefaultButton(self.w.okButton)

        self.w.open()

    def okCallback(self, sender):
        value = self.w.lineNumber.get()
        try:
            value = int(value.strip())
        except Exception:
            value = None
        self._callback(value)
        self.closeCallback(sender)

    def cancelCallback(self, sender):
        self._callback(None)
        self.closeCallback(sender)

    def closeCallback(self, sender):
        self.w.close()


def _hexToNSColor(color, default=AppKit.NSColor.blackColor()):
    if color is None:
        return default
    if len(color) != 6:
        return default
    r = int(color[0:2], 16) / 255.
    g = int(color[2:4], 16) / 255.
    b = int(color[4:6], 16) / 255.
    return AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1)


def _hexStringToNSColor(txt, default=AppKit.NSColor.blackColor()):
    if not txt.startswith("#"):
        raise DrawBotError("Not a hex color, should start with '#'")
    return _hexToNSColor(txt[1:], default)


def _NSColorToHexString(color):
    color = color.colorUsingColorSpaceName_(AppKit.NSCalibratedRGBColorSpace)
    r = round(color.redComponent() * 255)
    g = round(color.greenComponent() * 255)
    b = round(color.blueComponent() * 255)
    return "#%02X%02X%02X" % (r, g, b)


def _reverseMap(sourceMap):
    destMap = dict()
    for key, item in sourceMap.items():
        destMap[item] = key
    return destMap


_textAttributesForStyleCache = {}


def _clearTextAttributesForStyleCache():
    _textAttributesForStyleCache.clear()


def _textAttributesForStyle(style, font=None, token=None):
    if font is None:
        font = getFontDefault("PyDEFont", fallbackFont)
    if token and token in _textAttributesForStyleCache:
        return _textAttributesForStyleCache[token]
    attr = {
        AppKit.NSLigatureAttributeName: 0,
        AppKit.NSParagraphStyleAttributeName: basicParagraph,
    }
    if style.get("italic", False) and style.get("bold", False):
        fontManager = AppKit.NSFontManager.sharedFontManager()
        boldItalic = fontManager.convertFont_toHaveTrait_(font, AppKit.NSBoldFontMask | AppKit.NSItalicFontMask)
        if boldItalic is not None:
            font = boldItalic
    elif style.get("italic", False):
        fontManager = AppKit.NSFontManager.sharedFontManager()
        italic = fontManager.convertFont_toHaveTrait_(font, AppKit.NSItalicFontMask)
        if italic is not None:
            font = italic
    elif style.get("bold", False):
        fontManager = AppKit.NSFontManager.sharedFontManager()
        bold = fontManager.convertFont_toHaveTrait_(font, AppKit.NSBoldFontMask)
        if bold is not None:
            font = bold
    attr[AppKit.NSFontAttributeName] = font

    if style.get("color", False):
        attr[AppKit.NSForegroundColorAttributeName] = style["color"]
    if style.get("bgcolor", False):
        attr[AppKit.NSBackgroundColorAttributeName] = style["bgcolor"]
    if style.get("underline", False):
        attr[AppKit.NSUnderlineStyleAttributeName] = AppKit.NSUnderlineStyleSingle
        if style["color"]:
            attr[AppKit.NSUnderlineColorAttributeName] = style["color"]
    if token:
        _textAttributesForStyleCache[token] = attr
    return attr


_multiLineRE = re.compile(
    r"(\'\'\'|\"\"\"|/\*|<!--)"
    r".*?"
    r"(\'\'\'|\"\"\"|\*/|--!>)",
    re.DOTALL
)

_multiLineParts = [
    "\'\'\'",
    "\"\"\"",
    "\*", "*/",
    "<!--", "--!>"
    "# >>>", "# <<<",
]

_whiteSpaceRE = re.compile(r"[ \t]+")

_quoteFinderRE = re.compile(r'([\"\'])((?:(?!\1)[^\\]|(?:\\\\)*\\[^\\])*)\1')


def _findWhitespace(s, pos=0):
    m = _whiteSpaceRE.match(s, pos)
    if m is None:
        return pos
    return m.end()


def _pythonWordCompletions(text, charRange):
    if not hasJedi:
        return [], 0
    partialString = text.substringWithRange_(charRange)
    if not partialString:
        return [], 0
    keyWords = list(_drawBotDrawingTool.__all__)
    try:
        lines = text.substringWithRange_((0, charRange.location))
        lineCount = lines.count("\n") + 1
        if text.length() == charRange.location:
            columns = None
        else:
            columns = 0
            if text:
                while text.substringWithRange_((charRange.location - columns, 1)) != "\n":
                    if charRange.location - columns + 1 <= 1:
                        break
                    columns += 1
        script = jedi.api.Script(source=text)
        keyWords += [c.name for c in script.complete(line=lineCount, column=columns)]
    except Exception:
        import traceback
        traceback.print_exc()
    keyWords = [word for word in sorted(keyWords) if word.startswith(partialString)]
    return keyWords, 0


languagesIDEBehavior = {
    "Python": {
        "openToCloseMap": {"(": ")", "[": "]", "{": "}", "<": ">"},
        "autoCloseMap": {"(": ")", "[": "]", "{": "}", "\"": "\"", "'": "'"},
        "indentWithEndOfLine": [":", "(", "[", "{"],
        "comment": "#",
        "keywords": kwlist,
        "wordCompletions": _pythonWordCompletions,
        "dropPathFormatting": '%r',
        "dropPathsFormatting": '[%s]',
        "dropPathsSeperator": ", "
    },
}
languagesIDEBehavior["Python 3"] = languagesIDEBehavior["Python"]

downArrowSelectionDirection = 0
upArrowSelectionDirection = 1

def _floatRepr(f):
    """In Python 3, we may get float representations that are too precise,
    like 0.199999999999999. That is not nice for our interactive number
    editing."""
    return str(round(f, 8))


class CodeNSTextView(AppKit.NSTextView):

    jumpToLineWindowClass = _JumpToLineSheet

    def init(self):
        self = super(CodeNSTextView, self).init()
        self._highlightStyle = DefaultStyle
        self._languagesIDEBehavior = dict()
        self._fallbackTextColor = fallbackTextColor
        self._fallbackBackgroundColor = fallbackBackgroundColor
        self._fallbackHightLightColor = fallbackHightLightColor
        self._fallbackFont = fallbackFont

        self.setTypingAttributes_(_textAttributesForStyle(dict(color=self._fallbackTextColor)))
        self.setUsesFontPanel_(False)
        self.setRichText_(False)
        self.setAllowsUndo_(True)
        try:
            self.setUsesFindBar_(True)
        except Exception:
            self.setUsesFindPanel_(True)

        self._usesTabs = False
        self._indentSize = 4

        self._ignoreProcessEditing = False
        self._lexer = None
        self.highlightStyleMap = dict()

        nc = AppKit.NSNotificationCenter.defaultCenter()
        nc.addObserver_selector_name_object_(self, "userDefaultChanged:", "drawBotUserDefaultChanged", None)

        self._arrowSelectionDirection = None
        self._canDrag = False

        self._liveCoding = False

        return self

    def __del__(self):
        nc = AppKit.NSNotificationCenter.defaultCenter()
        nc.removeObserver_(self)

    def setLexer_(self, lexer):
        if lexer is None:
            raise "Cannot set a None type for lexer, must be a subclass of pygment Lexer."
        self._lexer = lexer
        if self.window():
            self.resetHighLightSyntax()

    def lexer(self):
        return self._lexer

    def setHighlightStyle_(self, style):
        self._highlightStyle = style
        self._buildhighlightStyleMap()
        if self.window():
            self.resetHighLightSyntax()

    def highlightStyle(self):
        return self._highlightStyle

    def setLanguagesIDEBehavior_(self, languagesIDEBehavior):
        self._languagesIDEBehavior = languagesIDEBehavior

    def languagesIDEBehavior(self):
        return self._languagesIDEBehavior

    def languagesIDEBehaviorForLanguage_(self, language):
        return self._languagesIDEBehavior.get(language)

    def _buildhighlightStyleMap(self):
        # cache all tokens with nscolors
        styles = self.highlightStyle()
        backgroundColor = _hexStringToNSColor(styles.background_color, self._fallbackBackgroundColor)
        self.setBackgroundColor_(backgroundColor)
        selectionColor = _hexStringToNSColor(styles.highlight_color, self._fallbackHightLightColor)
        self.setSelectedTextAttributes_({AppKit.NSBackgroundColorAttributeName: selectionColor})

        self.highlightStyleMap = dict()

        for token, style in styles:
            for key in "color", "bgcolor", "border":
                style[key] = _hexToNSColor(style[key], None)
            self.highlightStyleMap[token] = style

    def setUsesTabs_(self, usesTabs):
        oldIndent = self.indent()
        self._usesTabs = usesTabs
        newIndent = self.indent()

        string = self.string()
        string = string.replace(oldIndent, newIndent)
        self.setString_(string)

    def usesTabs(self):
        return self._usesTabs

    def setWrapWord_(self, value):
        if value:
            self.setHorizontallyResizable_(True)
            frame = self.visibleRect()
            self.setMaxSize_((frame.size.width, MAXFLOAT))
            self.textContainer().setWidthTracksTextView_(True)
            self.textContainer().setContainerSize_((frame.size.width, MAXFLOAT))
            if not hasattr(self.enclosingScrollView(), "placard"):
                self.enclosingScrollView().setHasHorizontalScroller_(False)
        else:
            self.setHorizontallyResizable_(True)
            self.setMaxSize_((MAXFLOAT, MAXFLOAT))
            self.textContainer().setWidthTracksTextView_(False)
            self.textContainer().setContainerSize_((MAXFLOAT, MAXFLOAT))
            self.enclosingScrollView().setHasHorizontalScroller_(True)
        if self.enclosingScrollView().hasVerticalRuler():
            self.enclosingScrollView().verticalRulerView().textDidChange_(self)

    def wrapWord(self):
        return self.maxSize() != (MAXFLOAT, MAXFLOAT)

    def setIndentSize_(self, size):
        oldIndent = oldIndent = self.indent()
        self._indentSize = size
        newIndent = self.indent()

        if not self.usesTabs():
            string = self.string()
            string = string.replace(oldIndent, newIndent)
            self.setString_(string)

    def indentSize(self):
        return self._indentSize

    def indent(self):
        if self.usesTabs():
            return "\t"
        else:
            return " " * self.indentSize()

    # overwritting NSTextView methods

    def setBackgroundColor_(self, color):
        # invert the insertioin pointer color
        # and the fallback text color and background color
        color = color.colorUsingColorSpaceName_(AppKit.NSCalibratedRGBColorSpace)
        r = color.redComponent()
        g = color.greenComponent()
        b = color.blueComponent()
        s = sum([r, g, b]) / 3.
        inverseColor = s < .6
        if inverseColor:
            self._fallbackBackgroundColor = AppKit.NSColor.blackColor()
            self._fallbackTextColor = AppKit.NSColor.whiteColor()
            self.setInsertionPointColor_(AppKit.NSColor.whiteColor())
        else:
            self._fallbackBackgroundColor = AppKit.NSColor.whiteColor()
            self._fallbackTextColor = AppKit.NSColor.blackColor()
            self.setInsertionPointColor_(AppKit.NSColor.blackColor())

        if self.enclosingScrollView():
            self.enclosingScrollView().setBackgroundColor_(color)
        self._updateRulersColors()
        super(CodeNSTextView, self).setBackgroundColor_(color)

    def changeColor_(self, color):
        # prevent external color overwrite,
        pass

    def changeAttributes_(self, attr):
        # prevent external attributes overwrite
        pass

    def smartInsertDeleteEnabled(self):
        return False

    def isAutomaticTextReplacementEnabled(self):
        return False

    def isAutomaticQuoteSubstitutionEnabled(self):
        return False

    def isAutomaticLinkDetectionEnabled(self):
        return False

    def isAutomaticDataDetectionEnabled(self):
        return False

    def isAutomaticDashSubstitutionEnabled(self):
        return False

    def isAutomaticSpellingCorrectionEnabled(self):
        return False

    # hightlighting

    def resetHighLightSyntax(self):
        self._ignoreProcessEditing = True
        self._highlightSyntax(0, self.string())
        self._ignoreProcessEditing = False

    @python_method
    def _highlightSyntax(self, location, text):
        if self.lexer() is None:
            return
        font = getFontDefault("PyDEFont", self._fallbackFont)
        length = self.string().length()
        setAttrs = self.textStorage().setAttributes_range_
        if text.endswith("\n"):
            text = text[:-1]
        # setAttrs = self.layoutManager().addTemporaryAttributes_forCharacterRange_
        self.textStorage().beginEditing()
        totLenValue = 0
        bigUnicodeAdd = 0
        for pos, token, value in self.lexer().get_tokens_unprocessed(text):
            style = self.highlightStyleMap.get(token)
            lenValue = len(value)
            bigUnicodeValue = nsStringLength(value)
            if location + pos + bigUnicodeValue > length:
                bigUnicodeValue = length - (location + pos)
            if bigUnicodeValue > 0:
                setAttrs(_textAttributesForStyle(style, font), (location + pos + bigUnicodeAdd, bigUnicodeValue))
                totLenValue += lenValue
                bigUnicodeAdd += bigUnicodeValue - lenValue
        self.textStorage().fixFontAttributeInRange_((location, totLenValue + bigUnicodeAdd))
        self.textStorage().endEditing()

    # key down

    def keyDown_(self, event):
        char = event.characters()
        selectedRange = self.selectedRange()
        if AppKit.NSEvent.modifierFlags() & AppKit.NSCommandKeyMask and selectedRange and char in (AppKit.NSUpArrowFunctionKey, AppKit.NSDownArrowFunctionKey, AppKit.NSLeftArrowFunctionKey, AppKit.NSRightArrowFunctionKey):
            value = self._getSelectedValueForRange(selectedRange)
            if value is not None:
                altDown = AppKit.NSEvent.modifierFlags() & AppKit.NSAlternateKeyMask
                shiftDown = AppKit.NSEvent.modifierFlags() & AppKit.NSShiftKeyMask
                altDown = AppKit.NSEvent.modifierFlags() & AppKit.NSAlternateKeyMask

                add = 1
                if altDown:
                    add = .1

                if char == AppKit.NSDownArrowFunctionKey:
                    add *= -1
                elif char == AppKit.NSLeftArrowFunctionKey:
                    add *= -1

                if shiftDown and altDown:
                    add /= 10
                elif shiftDown:
                    add *= 10

                if isinstance(value, tuple):
                    valueX, valueY = value
                    if char in [AppKit.NSUpArrowFunctionKey, AppKit.NSDownArrowFunctionKey]:
                        valueY += add
                    else:
                        valueX += add
                    value = "%s, %s" % (_floatRepr(valueX), _floatRepr(valueY))
                else:
                    value += add
                    value = _floatRepr(value)
                self._insertTextAndRun("%s" % value, selectedRange)
                return

            txt = self.string().substringWithRange_(selectedRange)
            if txt == "True":
                self._insertTextAndRun("False", selectedRange)
                return
            if txt == "False":
                self._insertTextAndRun("True", selectedRange)
                return
        lexer = self.lexer()
        if lexer is not None:
            languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
            if languageData and len(event.characters()) != 0:  # don't do magic if we've got a deadkey
                # get the auto close map based on the given lexer
                autoCloseMap = languageData.get("autoCloseMap", dict())
                # try to get the prev char, fail silently
                prevChar = ""
                if selectedRange.location >= 1:
                    try:
                        prevChar = self.string().substringWithRange_((selectedRange.location - 1, 1))
                    except IndexError:
                        # fail silently
                        pass
                prevChar = prevChar.strip()
                # try to get the next char, fail silently
                nextChar = ""
                try:
                    nextChar = self.string().substringWithRange_((selectedRange.location, 1))
                except IndexError:
                    # fail silently
                    pass
                nextChar = nextChar.strip()
                if char in "\"'":
                    if prevChar != char:
                        # special python case triple quotes
                        triplets = ""
                        try:
                            triplets = self.string().substringWithRange_((selectedRange.location, 3))
                        except IndexError:
                            # fail silently
                            pass
                        triplets = triplets.strip()
                        if triplets == char * 3:
                            # jump the cursor after the triple quotes
                            self.setSelectedRange_((selectedRange.location + 3, 0))
                            return
                        if nextChar == char:
                            # jump the cursor after a quote
                            self.setSelectedRange_((selectedRange.location + 1, 0))
                            return
                        if prevChar and (prevChar not in autoCloseMap or prevChar in "\"'") and selectedRange.length == 0:
                            # dont auto close
                            self.insertText_(char)
                            return
                # the the typed char is the same as the next char
                # and the char is part of the auto close map
                if char == nextChar and char in autoCloseMap.values():
                    reverseMap = {v: k for k, v in autoCloseMap.items()}
                    if reverseMap[char] != char:
                        # just jump the cursor if the char is not in the reversed auto close map
                        # adjust the cursor
                        self.setSelectedRange_((selectedRange.location + 1, 0))
                        return
                # reset the next char if it part of the auto close map
                if nextChar in autoCloseMap.values():
                    nextChar = ""
                # the typed char is in the auto close map
                if char in autoCloseMap:
                    # get the selected text
                    selectedText = self.string().substringWithRange_(selectedRange)
                    selectedText = selectedText.strip()
                    # if there is no next char
                    # or when there is a text selected
                    if not nextChar or selectedText:
                        # get the closing char
                        closeChar = autoCloseMap[char]
                        # construct text with auto closed chars
                        toInsert = char + selectedText + closeChar
                        # insert the text
                        self.insertText_(toInsert)
                        # reset the selection
                        if not selectedText:
                            selectedRange.location += 1
                            selectedRange.length = 0
                        else:
                            selectedRange.length = nsStringLength(toInsert)
                        self.setSelectedRange_(selectedRange)
                        return
        # perform the default behaviour of the text view
        super(CodeNSTextView, self).keyDown_(event)
        selectedRange = self.selectedRange()
        self._balanceParenForChar(char, selectedRange.location)
        if self.isLiveCoding():
            self.performSelectorInBackground_withObject_("_runInternalCode", None)

    def flagsChanged_(self, event):
        self._arrowSelectionDirection = None
        super(CodeNSTextView, self).flagsChanged_(event)

    def mouseDown_(self, event):
        self._canDrag = False
        if AppKit.NSEvent.modifierFlags() & AppKit.NSCommandKeyMask and self.selectedRange():
            self._canDrag = True
            self.undoManager().beginUndoGrouping()
            selRng = self.selectedRange()
            txt = self.string().substringWithRange_(selRng)
            if txt == "True":
                self._insertTextAndRun("False", selRng)
            elif txt == "False":
                self._insertTextAndRun("True", selRng)
            return
        super(CodeNSTextView, self).mouseDown_(event)

    def mouseDragged_(self, event):
        if self._canDrag:
            try:
                selRng = self.selectedRange()
                value = self._getSelectedValueForRange(selRng)
                if value is not None:
                    altDown = event.modifierFlags() & AppKit.NSAlternateKeyMask
                    shiftDown = event.modifierFlags() & AppKit.NSShiftKeyMask
                    altDown = event.modifierFlags() & AppKit.NSAlternateKeyMask
                    add = 1
                    if altDown and shiftDown:
                        add = .01
                    elif altDown:
                        add = .1
                    elif shiftDown:
                        add = 10

                    if isinstance(value, tuple):
                        valueX, valueY = value
                        valueX += int(event.deltaX() * 2) * add
                        valueY -= int(event.deltaY() * 2) * add
                        txtValue = "%s, %s" % (_floatRepr(valueX), _floatRepr(valueY))
                    else:
                        value += int(event.deltaX() * 2) * add
                        txtValue = "%s" % _floatRepr(value)

                    self._insertTextAndRun(txtValue, selRng)
            except Exception:
                pass
        super(CodeNSTextView, self).mouseDragged_(event)

    def mouseUp_(self, event):
        if self._canDrag:
            self.undoManager().endUndoGrouping()
        super(CodeNSTextView, self).mouseUp_(event)

    def insertTab_(self, sender):
        string = self.string()
        if string:
            selectedRange = self.selectedRange()
            try:
                char = string[selectedRange.location - 1]
            except IndexError:
                char = ""
            if char == ".":
                self.setSelectedRange_((selectedRange.location - 1, 1))
                self.insertText_("self.")
                return
        if self.usesTabs():
            return super(CodeNSTextView, self).insertTab_(sender)
        self.insertText_(self.indent())

    def insertNewline_(self, sender):
        selectedRange = self.selectedRange()
        super(CodeNSTextView, self).insertNewline_(sender)
        if self.lexer() is None:
            return
        languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
        if languageData:
            leadingSpace = ""
            line, lineRange = self._getTextForRange(selectedRange)
            m = _whiteSpaceRE.match(line)
            if m is not None:
                leadingSpace = m.group()
            # strip comment
            commentTag = languageData.get("comment")
            if commentTag is not None:
                line = line.split(commentTag)[0]
            line = line.strip()
            if line and line[-1] in languageData["indentWithEndOfLine"]:
                leadingSpace += self.indent()

            if leadingSpace:
                self.insertText_(leadingSpace)

    def deleteBackward_(self, sender):
        if self.lexer() is None:
            super(CodeNSTextView, self).deleteBackward_(sender)
            return
        languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
        if languageData:
            selectedRange = self.selectedRange()
            if selectedRange.length == 0:
                try:
                    char = self.string().substringWithRange_((selectedRange.location - 1, 1))
                    nextChar = self.string().substringWithRange_((selectedRange.location, 1))
                except IndexError:
                    char = nextChar = ""
                autoCloseMap = languageData.get("autoCloseMap", dict())
                if autoCloseMap.get(char) == nextChar:
                    self.setSelectedRange_((selectedRange.location - 1, 2))

        self._deleteIndentation(sender, False, super(CodeNSTextView, self).deleteBackward_)

    def deleteForward_(self, sender):
        self._deleteIndentation(sender, True, super(CodeNSTextView, self).deleteForward_)

    def moveLeft_(self, sender):
        super(CodeNSTextView, self).moveLeft_(sender)
        string = self.string()
        if not string:
            return
        selectedRange = self.selectedRange()
        char = string.substringWithRange_((selectedRange.location, 1))
        self._balanceParenForChar(char, selectedRange.location + 1)

    def moveRight_(self, sender):
        super(CodeNSTextView, self).moveRight_(sender)
        string = self.string()
        if not string:
            return
        selectedRange = self.selectedRange()
        char = string.substringWithRange_((selectedRange.location - 1, 1))
        self._balanceParenForChar(char, selectedRange.location)

    def moveWordLeft_(self, sender):
        ranges = self.selectedRanges()
        if len(ranges) == 1:
            newRange = ranges[0].rangeValue()
            location = self._getLeftWordRange(newRange)
            self.setSelectedRange_((location, 0))
        else:
            super(CodeNSTextView, self).moveWordLeft_(sender)

    def moveWordLeftAndModifySelection_(self, sender):
        ranges = self.selectedRanges()
        if self._arrowSelectionDirection is None:
            self._arrowSelectionDirection = downArrowSelectionDirection
        if len(ranges) == 1:
            newRange = ranges[0].rangeValue()
            testLocation = 0xFFFFFFFB
            if newRange.length and self._arrowSelectionDirection != downArrowSelectionDirection:
                testLocation = self._getLeftWordRange(AppKit.NSRange(newRange.location + newRange.length, 0))
            if AppKit.NSLocationInRange(testLocation, newRange) or AppKit.NSMaxRange(newRange) == testLocation:
                newRange = AppKit.NSRange(newRange.location, testLocation - newRange.location)
            else:
                location = self._getLeftWordRange(newRange)
                newRange = AppKit.NSRange(location, newRange.location - location + newRange.length)
            if newRange.length == 0:
                self._arrowSelectionDirection = None
            self.setSelectedRange_(newRange)
        else:
            super(CodeNSTextView, self).moveWordLeftAndModifySelection_(sender)

    def moveWordRight_(self, sender):
        ranges = self.selectedRanges()
        if len(ranges) == 1:
            newRange = ranges[0].rangeValue()
            location = self._getRightWordRange(newRange)
            self.setSelectedRange_((location, 0))
        else:
            super(CodeNSTextView, self).moveWordRight_(sender)

    def moveWordRightAndModifySelection_(self, sender):
        ranges = self.selectedRanges()
        if self._arrowSelectionDirection is None:
            self._arrowSelectionDirection = upArrowSelectionDirection
        if len(ranges) == 1:
            newRange = ranges[0].rangeValue()
            testLocation = 0xFFFFFFFB
            if newRange.length and self._arrowSelectionDirection != upArrowSelectionDirection:
                testLocation = self._getRightWordRange(AppKit.NSRange(newRange.location, 0))
            if AppKit.NSLocationInRange(testLocation, newRange) or AppKit.NSMaxRange(newRange) == testLocation:
                newRange = AppKit.NSRange(testLocation, newRange.location - testLocation + newRange.length)
            else:
                location = self._getRightWordRange(newRange)
                newRange = AppKit.NSRange(newRange.location, location - newRange.location)
            if newRange.length == 0:
                self._arrowSelectionDirection = None
            self.setSelectedRange_(newRange)
        else:
            super(CodeNSTextView, self).moveWordRightAndModifySelection_(sender)

    def deleteWordBackward_(self, sender):
        ranges = self.selectedRanges()
        if len(ranges) == 1:
            newRange = ranges[0].rangeValue()
            if newRange.length == 0:
                self.moveWordLeftAndModifySelection_(sender)
        super(CodeNSTextView, self).deleteWordForward_(sender)

    def deleteWordForward_(self, sender):
        ranges = self.selectedRanges()
        if len(ranges) == 1:
            newRange = ranges[0].rangeValue()
            if newRange.length == 0:
                self.moveWordRightAndModifySelection_(sender)
        super(CodeNSTextView, self).deleteWordForward_(sender)

    # text completion

    def cancelOperation_(self, sender):
        self.complete_(sender)

    def rangeForUserCompletion(self):
        charRange = super(CodeNSTextView, self).rangeForUserCompletion()
        text = self.string()
        partialString = text.substringWithRange_(charRange)
        if "." in partialString:
            dotSplit = partialString.split(".")
            partialString = dotSplit.pop()
            move = len(".".join(dotSplit))
            charRange.location += move + 1
            charRange.length = len(partialString)
        for c in partialString:
            if c not in variableChars:
                return (AppKit.NSNotFound, 0)
        return charRange

    def completionsForPartialWordRange_indexOfSelectedItem_(self, charRange, index):
        if self.lexer() is None:
            return [], 0
        languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
        if languageData is None:
            return [], 0
        text = self.string()
        func = languageData.get("wordCompletions", self._genericCompletions)
        return func(text, charRange)

    @python_method
    def _genericCompletions(self, text, charRange):
        partialString = text.substringWithRange_(charRange)
        keyWords = list()
        index = 0
        languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
        if languageData is None:
            return keyWords, index
        if partialString:
            _reWords = re.compile(r"\b%s\w+\b" % partialString)
            keyWords = _reWords.findall(text)
            keyWords = list(set(keyWords + languageData.get("keywords", [])))
            keyWords = [word for word in sorted(keyWords) if word.startswith(partialString)]
        return keyWords, index

    def selectionRangeForProposedRange_granularity_(self, proposedRange, granularity):
        location = proposedRange.location
        if granularity == AppKit.NSSelectByWord and proposedRange.length == 0 and location != 0:
            text = self.string()
            lenText = text.length()
            length = 1
            found = False
            while not found:
                location -= 1
                length += 1
                if location <= 0:
                    found = True
                else:
                    c = text.substringWithRange_((location, 1))[0]
                    if c not in variableChars:
                        location += 1
                        found = True
            found = False
            while not found:
                length += 1
                if location + length > lenText:
                    found = True
                else:
                    c = text.substringWithRange_((location, length))[-1]
                    if c not in variableChars:
                        length -= 1
                        found = True
            return location, length
        else:
            return super(CodeNSTextView, self).selectionRangeForProposedRange_granularity_(proposedRange, granularity)

    # drop

    def acceptableDragTypes(self):
        acceptableDragTypes = super(CodeNSTextView, self).acceptableDragTypes()
        return list(acceptableDragTypes) + [AppKit.NSFilenamesPboardType]

    def readSelectionFromPasteboard_type_(self, pboard, pbType):
        if pbType == AppKit.NSFilenamesPboardType:
            languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
            if languageData is not None:
                formatter = languageData.get("dropPathFormatting")
                if formatter:
                    paths = pboard.propertyListForType_(AppKit.NSFilenamesPboardType)
                    dropText = ""
                    if len(paths) == 1:
                        dropText = formatter % paths[0]
                    else:
                        formattedPaths = []
                        for path in paths:
                            formattedPaths.append(formatter % path)

                        multiLineFormater = languageData.get("dropPathsFormatting", "%s")
                        seperator = languageData.get("dropPathsSeperator", "\n")
                        dropText = multiLineFormater % seperator.join(formattedPaths)

                    if dropText:
                        self.insertText_(dropText)
                        return True
        return super(CodeNSTextView, self).readSelectionFromPasteboard_type_(pboard, pbType)

    # menu

    def wrapWord_(self, sender):
        self.setWrapWord_(not self.wrapWord())

    def indent_(self, sender):
        def indentFilter(lines):
            indent = self.indent()
            indentedLines = []
            for line in lines:
                if line.strip():
                    indentedLines.append(indent + line)
                else:
                    indentedLines.append(line)
            [indent + line for line in lines[:-1]]
            return indentedLines
        self._filterLines(indentFilter)

    def dedent_(self, sender):
        def dedentFilter(lines):
            indent = self.indent()
            dedentedLines = []
            indentSize = len(indent)
            for line in lines:
                if line.startswith(indent):
                    line = line[indentSize:]
                dedentedLines.append(line)
            return dedentedLines
        self._filterLines(dedentFilter)

    def comment_(self, sender):
        def commentFilter(lines):
            languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
            if languageData is None:
                return lines
            commentTag = languageData.get("comment")
            if commentTag is None:
                return lines
            commentTag += " "
            commentEndTag = languageData.get("commentEnd", "")
            if commentEndTag:
                commentEndTag = " " + commentEndTag
            commentedLines = []
            pos = 100
            for line in lines:
                if not line.strip():
                    continue
                pos = min(pos, _findWhitespace(line))
            for line in lines:
                if line.strip():
                    addEnd = ""
                    if line[-1] == "\n":
                        line = line.replace("\n", "")
                        addEnd = "\n"
                    commentedLines.append(line[:pos] + commentTag + line[pos:] + commentEndTag + addEnd)
                else:
                    commentedLines.append(line)
            return commentedLines
        self._filterLines(commentFilter)

    def uncomment_(self, sender):
        def uncommentFilter(lines):
            languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
            if languageData is None:
                return lines
            commentTag = languageData.get("comment", "")
            commentEndTag = languageData.get("commentEnd", "")
            _commentRE = re.compile(r"[ \t]*(%s)[ ]?" % commentTag)

            commentedLines = []
            commentMatch = _commentRE.match
            for line in lines:
                m = commentMatch(line)
                if m is not None:
                    start = m.start(1)
                    end = m.end()
                    line = line[:start] + line[end:]
                    line = line.replace(commentEndTag, "")
                commentedLines.append(line)
            return commentedLines
        self._filterLines(uncommentFilter)

    @python_method
    def _jumpToLine(self, lineNumber):
        lines = 1
        string = self.string()
        length = string.length()
        tempRange = AppKit.NSMakeRange(0, length)
        found = None
        while tempRange.location < length:
            tempRange = string.lineRangeForRange_(AppKit.NSMakeRange(tempRange.location, 0))
            if lines == lineNumber:
                found = tempRange
                break
            tempRange.location = AppKit.NSMaxRange(tempRange)
            lines += 1

        if found:
            self.setSelectedRange_(found)
            self.scrollRangeToVisible_(found)

    def jumpToLine_(self, sender):
        self.jumpToLineWindowClass(self._jumpToLine, self.window())

    def jumpToLineNumber_(self, lineNumber):
        self._jumpToLine(lineNumber)

    def liveCoding_(self, sender):
        self._liveCoding = not self._liveCoding

    def isLiveCoding(self):
        return self._liveCoding

    def validateUserInterfaceItem_(self, item):
        if item.action() == "liveCoding:":
            item.setState_(self.isLiveCoding())
        return super(CodeNSTextView, self).validateUserInterfaceItem_(item)

    # notifications

    def textStorageDidProcessEditing_(self, notification):
        if self._ignoreProcessEditing:
            return
        string = self.string()
        if not string:
            # no text to color
            return
        length = string.length()
        textStorage = self.textStorage()
        _lineStart, _lineLength = textStorage.editedRange()
        editedString = string.substringWithRange_((_lineStart, _lineLength))
        for part in _multiLineParts:
            if part in editedString:
                _lineStart = 0
                _lineLength = length

        lineStart = _lineStart  # - 200
        lineLength = _lineLength  # + 200
        if lineStart <= 0:
            lineStart = 0
        if lineStart > length:
            lineStart = length
            lineLength = 0
        if lineStart + lineLength > length:
            lineLength = length - lineStart

        lineStart, lineLength = string.lineRangeForRange_((lineStart, lineLength))

        for quoteMatch in _multiLineRE.finditer(string):
            start, end = quoteMatch.start(), quoteMatch.end()
            quoteRange = (start, end - start)
            if AppKit.NSLocationInRange(_lineStart, quoteRange) or AppKit.NSLocationInRange(_lineStart + _lineLength, quoteRange):
                quoteStart, quoteLenght = string.lineRangeForRange_(quoteRange)
                lineStart, lineLength = AppKit.NSUnionRange(quoteRange, (_lineStart, _lineLength))
                break
        text = string.substringWithRange_((lineStart, lineLength))
        self._highlightSyntax(lineStart, text)

    def viewDidMoveToWindow(self):
        self._buildhighlightStyleMap()
        self.resetHighLightSyntax()
        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.addObserver_selector_name_object_(self, "textStorageDidProcessEditing:", AppKit.NSTextStorageDidProcessEditingNotification, self.textStorage())

    def dealloc(self):
        notificationCenter = AppKit.NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self)
        super(CodeNSTextView, self).dealloc()

    def userDefaultChanged_(self, notification):
        if self.window():
            _clearTextAttributesForStyleCache()
            style = styleFromDefault()
            self.setTypingAttributes_(_textAttributesForStyle(dict(color=self._fallbackTextColor)))
            self.setHighlightStyle_(style)

    # helpers

    def _updateRulersColors(self):
        scrollView = self.enclosingScrollView()
        if scrollView and scrollView.hasVerticalRuler():
            ruler = scrollView.verticalRulerView()
            if hasattr(ruler, "setTextColor_"):
                numberStyle = self.highlightStyleMap.get(Comment)
                if numberStyle:
                    ruler.setTextColor_(numberStyle["color"])
            if hasattr(ruler, "setRulerBackgroundColor_"):
                styles = self.highlightStyle()
                backgroundColor = _hexStringToNSColor(styles.background_color, self._fallbackBackgroundColor)
                ruler.setRulerBackgroundColor_(backgroundColor)

    @python_method
    def _deleteIndentation(self, sender, isForward, superFunc):
        selectedRange = self.selectedRange()
        if self.usesTabs() or selectedRange.length:
            return superFunc(sender)
        string = self.string()
        if not string:
            return superFunc(sender)
        possibleIndentStart = selectedRange.location - self.indentSize()
        possibleIndentEnd = self.indentSize()
        if isForward:
            possibleIndentStart = selectedRange.location

        if possibleIndentStart < 0:
            return superFunc(sender)
        possibleIndent = None
        if possibleIndentStart + possibleIndentEnd > string.length():
            return superFunc(sender)
        possibleIndent = string.substringWithRange_((possibleIndentStart, possibleIndentEnd))

        if possibleIndent == self.indent():
            self.setSelectedRange_((possibleIndentStart, possibleIndentEnd))
            self.insertText_("")
        else:
            superFunc(sender)

    @python_method
    def _findMatchingParen(self, location, char, matchChar, end):
        add = 1
        if end:
            add = -1
            location -= 2

        string = self.string()
        found = None
        stack = 0
        while location >= 0 and location < string.length():
            c = string.substringWithRange_((location, 1))
            if c == char:
                stack += 1
            elif stack != 0 and c == matchChar:
                stack -= 1
            elif c == matchChar:
                found = location
                break
            location += add
        return found

    @python_method
    def _balanceParenForChar(self, char, location):
        if self.lexer() is None:
            return
        languageData = self.languagesIDEBehaviorForLanguage_(self.lexer().name)
        if languageData is None:
            return
        openToCloseMap = languageData["openToCloseMap"]
        if char in openToCloseMap.keys():
            self._balanceParens(location=location, char=char, matchChar=openToCloseMap[char], end=False)
        elif char in openToCloseMap.values():
            openToCloseMap = _reverseMap(openToCloseMap)
            self._balanceParens(location=location, char=char, matchChar=openToCloseMap[char], end=True)

    @python_method
    def _balanceParens(self, location, char, matchChar, end):
        found = self._findMatchingParen(location, char, matchChar, end)
        if found is not None:
            oldAttrs, effRng = self.textStorage().attributesAtIndex_effectiveRange_(found, None)
            styles = self.highlightStyle()
            selectionColor = _hexStringToNSColor(styles.highlight_color, self._fallbackHightLightColor)
            textColor = oldAttrs.get(AppKit.NSForegroundColorAttributeName, self._fallbackTextColor)
            shadow = AppKit.NSShadow.alloc().init()
            shadow.setShadowOffset_((0, 0))
            shadow.setShadowColor_(textColor)
            shadow.setShadowBlurRadius_(3)
            balancingAttrs = {
                AppKit.NSBackgroundColorAttributeName: selectionColor,
                AppKit.NSShadowAttributeName: shadow
            }
            self.layoutManager().setTemporaryAttributes_forCharacterRange_(balancingAttrs, (found, 1))
            self.performSelector_withObject_afterDelay_("_resetBalanceParens:", (oldAttrs, effRng), 0.2)

    def _resetBalanceParens_(self, attrs_rng):
        attrs, rng = attrs_rng
        self.layoutManager().setTemporaryAttributes_forCharacterRange_(attrs, rng)

    @python_method
    def _filterLines(self, filterFunc):
        selectedRange = self.selectedRange()
        lines, linesRange = self._getTextForRange(selectedRange)

        filteredLines = filterFunc(lines.splitlines(True))

        filteredLines = "".join(filteredLines)
        if lines == filteredLines:
            return
        self.setSelectedRange_(linesRange)
        self.insertText_(filteredLines)
        newSelRng = linesRange.location, len(filteredLines)
        self.setSelectedRange_(newSelRng)

    @python_method
    def _getLeftWordRange(self, newRange):
        if newRange.location == 0:
            return 0
        text = self.string()
        location = newRange.location - 1

        c = text.substringWithRange_((location, 1))[0]
        isChar = foundChar = c in variableChars

        count = 0
        while isChar == foundChar:
            count += 1
            location -= 1
            if location <= 0:
                location = 0
                foundChar = not isChar
            else:
                c = text.substringWithRange_((location, 1))[0]
                foundChar = c in variableChars
                if count == 1 and isChar != foundChar:
                    isChar = not isChar
        if location != 0:
            location += 1

        return location

    @python_method
    def _getRightWordRange(self, newRange):
        text = self.string()
        lenText = text.length()
        location = newRange.location + newRange.length
        if location >= lenText:
            return lenText

        count = 0
        c = text.substringWithRange_((location, 1))[0]
        isChar = foundChar = c in variableChars
        while isChar == foundChar:
            count += 1
            location += 1
            if location >= lenText:
                location = lenText
                foundChar = not isChar
            else:
                c = text.substringWithRange_((location, 1))[0]
                foundChar = c in variableChars
                if count == 1 and isChar != foundChar:
                    isChar = not isChar
        return location

    @python_method
    def _getTextForRange(self, lineRange):
        string = self.string()
        lineRange = string.lineRangeForRange_(lineRange)
        return string.substringWithRange_(lineRange), lineRange

    @python_method
    def _getSelectedValueForRange(self, selectedRange):
        value = None
        try:
            txt = self.string().substringWithRange_(selectedRange)
            for c in txt:
                if c not in "0123456789.,- ":
                    raise DrawBotError("No dragging possible")
            value = eval(txt)
        except Exception:
            pass
        return value

    @python_method
    def _insertTextAndRun(self, txt, txtRange):
        self.insertText_(txt)
        newRange = AppKit.NSMakeRange(txtRange.location, len(txt))
        self.setSelectedRange_(newRange)
        return self._runInternalCode()

    @python_method
    def _runInternalCode(self):
        pool = AppKit.NSAutoreleasePool.alloc().init()
        try:
            try:
                window = self.window()
                if window is not None:
                    doc = window.document()
                    if doc is not None:
                        doc.runCode_(self)
                        return True
            except Exception:
                return False
        finally:
            del pool


class CodeEditor(TextEditor):

    nsTextViewClass = CodeNSTextView

    def __init__(self, *args, **kwargs):
        codeAttr = dict()
        for key in "lexer", "highlightStyle", "usesTabs", "indentSize", "languagesIDEBehavior", "showlineNumbers":
            value = None
            if key in kwargs:
                value = kwargs.get(key)
                del kwargs[key]
            codeAttr[key] = value
        super(CodeEditor, self).__init__(*args, **kwargs)
        if isinstance(codeAttr["lexer"], str):
            try:
                codeAttr["lexer"] = get_lexer_by_name(codeAttr["lexer"])
            except Exception:
                codeAttr["lexer"] = None
        if codeAttr["lexer"] is None:
            codeAttr["lexer"] = Python3Lexer(encoding='utf-8')
        self.setLexer(codeAttr["lexer"])
        if codeAttr["highlightStyle"] is None:
            codeAttr["highlightStyle"] = styleFromDefault()
        if codeAttr["highlightStyle"] is not None:
            self.setHighlightStyle(codeAttr["highlightStyle"])
        if codeAttr["usesTabs"] is not None:
            self.setUsesTabs(codeAttr["usesTabs"])
        if codeAttr["indentSize"] is not None:
            self.setIndentSize(codeAttr["indentSize"])
        if codeAttr["languagesIDEBehavior"] is not None:
            _languagesIDEBehavior.update(codeAttr["languagesIDEBehavior"])
        self.setLanguagesIDEBehavior(languagesIDEBehavior)

        if codeAttr["showlineNumbers"] is None:
            codeAttr["showlineNumbers"] = True
        ruler = LineNumberNSRulerView.alloc().init()
        ruler.setClientView_(self.getNSTextView())
        ruler.setRulerBackgroundColor_(AppKit.NSColor.colorWithCalibratedWhite_alpha_(.95, 1))
        self.getNSScrollView().setVerticalRulerView_(ruler)
        self.getNSScrollView().setHasHorizontalRuler_(False)
        self.getNSScrollView().setHasVerticalRuler_(codeAttr["showlineNumbers"])
        self.getNSScrollView().setRulersVisible_(True)

    def setHighlightStyle(self, style):
        self.getNSTextView().setHighlightStyle_(style)

    def setLexer(self, lexer):
        self.getNSTextView().setLexer_(lexer)

    def setLanguagesIDEBehavior(self, languagesIDEBehavior):
        self.getNSTextView().setLanguagesIDEBehavior_(languagesIDEBehavior)

    def setUsesTabs(self, value):
        self.getNSTextView().setUsesTabs_(value)

    def usesTabs(self):
        return self.getNSTextView().usesTabs()

    def setIndentSize(self, value):
        self.getNSTextView().setIndentSize_(value)

    def indentSize(self):
        return self.getNSTextView().indentSize()

    def comment(self):
        self.getNSTextView().comment_(self)

    def uncomment(self):
        self.getNSTextView().uncomment_(self)

    def indent(self):
        self.getNSTextView().indent_(self)

    def dedent(self):
        self.getNSTextView().dedent_(self)

    def jumpToLine(self, lineNumber=None):
        if lineNumber is None:
            self.getNSTextView().jumpToLine_(self)
        else:
            self.getNSTextView().jumpToLineNumber_(lineNumber)

    def toggleLineNumbers(self):
        self.getNSScrollView().setHasVerticalRuler_(not self.getNSScrollView().hasVerticalRuler())

    def wrapWord(self, value):
        self.getNSTextView().setWrapWord_(value)


class OutPutCodeNSTextView(CodeNSTextView):

    def init(self):
        self = super(OutPutCodeNSTextView, self).init()
        self._items = []
        self.setTextAttributes()
        return self

    def clear(self):
        self._items = []
        self.setString_("")

    def appendText_isError_(self, text, isError):
        self._items.append((text, isError))
        attrs = self.textAttributes
        if isError:
            attrs = self.tracebackAttributes
        text = AppKit.NSAttributedString.alloc().initWithString_attributes_(text, attrs)
        self.textStorage().appendAttributedString_(text)

    def userDefaultChanged_(self, notification):
        super(OutPutCodeNSTextView, self).userDefaultChanged_(notification)
        self.setTextAttributes()

    def setTextAttributes(self):
        self.setString_("")

        styles = styleFromDefault()
        self.setHighlightStyle_(styles)
        self.textAttributes = outputTextAttributesForStyles(styles)
        self.tracebackAttributes = outputTextAttributesForStyles(styles, isError=True)

        backgroundColor = _hexStringToNSColor(styles.background_color, self._fallbackBackgroundColor)
        self.setBackgroundColor_(backgroundColor)
        selectionColor = _hexStringToNSColor(styles.highlight_color, self._fallbackHightLightColor)
        self.setSelectedTextAttributes_({AppKit.NSBackgroundColorAttributeName: selectionColor})

        self.setFont_(getFontDefault("PyDEFont", self._fallbackFont))

        items = self._items
        self._items = []
        for text, isError in items:
            self.appendText_isError_(text, isError)


class OutPutEditor(TextEditor):

    nsTextViewClass = OutPutCodeNSTextView

    def append(self, text, isError=False):
        self.getNSTextView().appendText_isError_(text, isError)

    def clear(self):
        self.getNSTextView().clear()

    def forceUpdate(self):
        self.getNSTextView().display()

    def scrollToEnd(self):
        self.getNSTextView().scrollRangeToVisible_((self.getNSTextView().string().length(), 0))
