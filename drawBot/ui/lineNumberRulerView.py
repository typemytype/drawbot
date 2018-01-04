from Foundation import NSInvocation, NSString, NSMakeRange, NSMaxRange, NSLocationInRange, NSNotFound, NSMakeRect, NSMinY, NSWidth, NSHeight
from AppKit import NSRulerView, NSMiniControlSize, NSTextView, NSNotificationCenter, \
    NSFontAttributeName, NSForegroundColorAttributeName, NSTextStorageDidProcessEditingNotification, \
    NSFont, NSColor, NSBezierPath, NSRectFill
import math
from objc import super


"""
Based/translated from NoodleLineNumberView
http://www.noodlesoft.com/blog/2008/10/05/displaying-line-numbers-with-nstextview/
"""


class LineNumberNSRulerView(NSRulerView):

    DEFAULT_THICKNESS = 22.
    RULER_MARGIN = 5.

    def init(self):
        self = super(LineNumberNSRulerView, self).init()
        self._font = NSFont.labelFontOfSize_(NSFont.systemFontSizeForControlSize_(NSMiniControlSize))
        self._textColor = NSColor.colorWithCalibratedWhite_alpha_(.42, 1)
        self._rulerBackgroundColor = None

        self._lineIndices = None
        return self

    def setFont_(self, font):
        self._font = font

    def font(self):
        return self._font

    def setTextColor_(self, color):
        self._textColor = color
        self.setNeedsDisplay_(True)

    def textColor(self):
        return self._textColor

    def textAttributes(self):
        return {
            NSFontAttributeName: self.font(),
            NSForegroundColorAttributeName: self.textColor()
        }

    def setRulerBackgroundColor_(self, color):
        self._rulerBackgroundColor = color
        self.setNeedsDisplay_(True)

    def rulerBackgroundColor(self):
        return self._rulerBackgroundColor

    def setClientView_(self, view):
        oldClientView = self.clientView()

        if oldClientView != view and isinstance(oldClientView, NSTextView):
            NSNotificationCenter.defaultCenter().removeObserver_name_object_(self, NSTextStorageDidProcessEditingNotification, oldClientView.textStorage())

        super(LineNumberNSRulerView, self).setClientView_(view)

        if view is not None and isinstance(view, NSTextView):
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, "textDidChange:",
                                                    NSTextStorageDidProcessEditingNotification,
                                                    view.textStorage())

    def lineIndices(self):
        if self._lineIndices is None:
            self.calculateLines()
        return self._lineIndices

    def invalidateLineIndices(self):
        self._lineIndices = None

    def textDidChange_(self, sender):
        self.calculateLines()
        self.invalidateLineIndices()
        self.setNeedsDisplay_(True)

    def dealloc(self):
        # make sure we remove ourselves as an observer of the text storage
        view = self.clientView()
        if view is not None:
            NSNotificationCenter.defaultCenter().removeObserver_name_object_(self, NSTextStorageDidProcessEditingNotification, view.textStorage())
        super(LineNumberNSRulerView, self).dealloc()

    def calculateLines(self):
        view = self.clientView()
        if not isinstance(view, NSTextView):
            return

        text = view.string()
        textLength = text.length()

        if not textLength:
            self._lineIndices = [1]
            return

        lineIndices = []

        index = 0
        numberOfLines = 0
        while index < textLength:
            lineIndices.append(index)
            index = NSMaxRange(text.lineRangeForRange_(NSMakeRange(index, 0)))
            numberOfLines += 1

        lineStart, lineEnd, contentEnd = text.getLineStart_end_contentsEnd_forRange_(None, None, None, NSMakeRange(lineIndices[-1], 0))

        if contentEnd < lineEnd:
            lineIndices.append(index)

        self._lineIndices = lineIndices

        oldThickness = self.ruleThickness()
        newThickness = self.requiredThickness()

        if abs(oldThickness - newThickness) > 0:
            invocation = NSInvocation.invocationWithMethodSignature_(self.methodSignatureForSelector_("setRuleThickness:"))
            invocation.setSelector_("setRuleThickness:")
            invocation.setTarget_(self)
            invocation.setArgument_atIndex_(newThickness, 2)
            invocation.performSelector_withObject_afterDelay_("invoke", None, 0)

    def requiredThickness(self):
        lineCount = len(self.lineIndices())
        digits = int(math.log10(lineCount) + 1)

        sampleString = NSString.stringWithString_("8" * digits)
        stringSize = sampleString.sizeWithAttributes_(self.textAttributes())
        return math.ceil(max([self.DEFAULT_THICKNESS, stringSize.width + self.RULER_MARGIN * 2]))

    def lineNumberForCharacterIndex_inText_(self, index, text):
        lines = self.lineIndices()

        left = 0
        right = len(lines)

        while (right - left) > 1:
            mid = (right + left) // 2
            lineStart = lines[mid]

            if index < lineStart:
                right = mid
            elif index > lineStart:
                left = mid
            else:
                return mid

        return left

    def drawHashMarksAndLabelsInRect_(self, rect):
        bounds = self.bounds()
        view = self.clientView()

        rulerBackgroundColor = self.rulerBackgroundColor()
        if rulerBackgroundColor is not None:
            rulerBackgroundColor.set()
            NSRectFill(bounds)

        if not isinstance(view, NSTextView):
            return

        layoutManager = view.layoutManager()
        container = view.textContainer()
        text = view.string()
        nullRange = NSMakeRange(NSNotFound, 0)
        yinset = view.textContainerInset().height
        visibleRect = self.scrollView().contentView().bounds()
        textAttributes = self.textAttributes()

        lines = self.lineIndices()

        glyphRange = layoutManager.glyphRangeForBoundingRect_inTextContainer_(visibleRect, container)
        _range = layoutManager.characterRangeForGlyphRange_actualGlyphRange_(glyphRange, None)[0]
        _range.length += 1

        count = len(lines)
        index = 0

        lineNumber = self.lineNumberForCharacterIndex_inText_(_range.location, text)

        for line in range(lineNumber, count):
            index = lines[line]
            if NSLocationInRange(index, _range):
                rects, rectCount = layoutManager.rectArrayForCharacterRange_withinSelectedCharacterRange_inTextContainer_rectCount_(
                    NSMakeRange(index, 0),
                    nullRange,
                    container,
                    None
                )
                if rectCount > 0:
                    ypos = yinset + NSMinY(rects[0]) - NSMinY(visibleRect)
                    labelText = NSString.stringWithString_("%s" % (line + 1))
                    stringSize = labelText.sizeWithAttributes_(textAttributes)

                    x = NSWidth(bounds) - stringSize.width - self.RULER_MARGIN
                    y = ypos + (NSHeight(rects[0]) - stringSize.height) / 2.0
                    w = NSWidth(bounds) - self.RULER_MARGIN * 2.0
                    h = NSHeight(rects[0])

                    labelText.drawInRect_withAttributes_(NSMakeRect(x, y, w, h), textAttributes)

            if index > NSMaxRange(_range):
                break

        path = NSBezierPath.bezierPath()
        path.moveToPoint_((bounds.origin.x + bounds.size.width, bounds.origin.y))
        path.lineToPoint_((bounds.origin.x + bounds.size.width, bounds.origin.y + bounds.size.height))
        NSColor.grayColor().set()
        path.stroke()
