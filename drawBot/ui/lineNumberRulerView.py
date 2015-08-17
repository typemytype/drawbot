import math
import objc
import AppKit
NSMakeRange = AppKit.NSMakeRange
NSMaxRange = AppKit.NSMaxRange
NSLocationInRange = AppKit.NSLocationInRange


"""
Based/translated from NoodleLineNumberView
http://www.noodlesoft.com/blog/2008/10/05/displaying-line-numbers-with-nstextview/
"""


class NSLineNumberRuler(AppKit.NSRulerView):

    DEFAULT_THICKNESS = 22.
    RULER_MARGIN = 5.

    def init(self):
        self = objc.super(NSLineNumberRuler, self).init()
        self._font = AppKit.NSFont.labelFontOfSize_(AppKit.NSFont.systemFontSizeForControlSize_(AppKit.NSMiniControlSize))
        self._textColor = AppKit.NSColor.colorWithCalibratedWhite_alpha_(.42, 1)
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
                AppKit.NSFontAttributeName: self.font(),
                AppKit.NSForegroundColorAttributeName: self.textColor()
                }

    def setRulerBackgroundColor_(self, color):
        self._rulerBackgroundColor = color
        self.setNeedsDisplay_(True)

    def rulerBackgroundColor(self):
        return self._rulerBackgroundColor

    def setClientView_(self, view):
        oldClientView = self.clientView()

        if oldClientView != view and isinstance(oldClientView, AppKit.NSTextView):
            NSNotificationCenter.defaultCenter().removeObserver_name_object_(self, AppKit.NSTextStorageDidProcessEditingNotification, oldClientView.textStorage())

        objc.super(NSLineNumberRuler, self).setClientView_(view)

        if view is not None and isinstance(view, AppKit.NSTextView):
            AppKit.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, "textDidChange:",
                                                    AppKit.NSTextStorageDidProcessEditingNotification,
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

    def calculateLines(self):
        view = self.clientView()
        if not isinstance(view, AppKit.NSTextView):
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

        if abs(oldThickness - newThickness) > 1:
            invocation = AppKit.NSInvocation.invocationWithMethodSignature_(self.methodSignatureForSelector_("setRuleThickness:"))
            invocation.setSelector_("setRuleThickness:")
            invocation.setTarget_(self)
            invocation.setArgument_atIndex_(newThickness, 2)
            invocation.performSelector_withObject_afterDelay_("invoke", None, 0)

    def requiredThickness(self):
        lineCount = len(self.lineIndices())
        digits = int(math.log10(lineCount) + 1)

        sampleString = AppKit.NSString.stringWithString_("8"*digits)
        stringSize = sampleString.sizeWithAttributes_(self.textAttributes())
        return math.ceil(max([self.DEFAULT_THICKNESS, stringSize.width + self.RULER_MARGIN*2]))

    def lineNumberForCharacterIndex_inText_(self, index, text):
        lines = self.lineIndices()

        left = 0
        right = len(lines)

        while (right - left) > 1:
            mid = (right + left) / 2
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
            AppKit.NSRectFill(bounds)

        if not isinstance(view, AppKit.NSTextView):
            return

        layoutManager = view.layoutManager()
        container = view.textContainer()
        text = view.string()
        nullRange = NSMakeRange(AppKit.NSNotFound, 0)
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
                    ypos = yinset + AppKit.NSMinY(rects[0]) - AppKit.NSMinY(visibleRect)
                    labelText = AppKit.NSString.stringWithString_("%s" % (line+1))
                    stringSize = labelText.sizeWithAttributes_(textAttributes)

                    x = AppKit.NSWidth(bounds) - stringSize.width - self.RULER_MARGIN
                    y = ypos + (AppKit.NSHeight(rects[0]) - stringSize.height) / 2.0
                    w = AppKit.NSWidth(bounds) - self.RULER_MARGIN * 2.0
                    h = AppKit.NSHeight(rects[0])

                    labelText.drawInRect_withAttributes_(AppKit.NSMakeRect(x, y, w, h), textAttributes)

            if index > NSMaxRange(_range):
                break

        path = AppKit.NSBezierPath.bezierPath()
        path.moveToPoint_((bounds.origin.x+bounds.size.width, bounds.origin.y))
        path.lineToPoint_((bounds.origin.x+bounds.size.width, bounds.origin.y+bounds.size.height))
        AppKit.NSColor.grayColor().set()
        path.stroke()
