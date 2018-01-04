from AppKit import NSSplitView, NSColor, NSBezierPath, \
    NSSplitViewDividerStyleThick, NSSplitViewDividerStyleThin
from objc import super

from vanilla import *
from vanilla.vanillaBase import VanillaBaseObject


class SimpleNSSplitView(NSSplitView):

    def init(self):
        self = super(SimpleNSSplitView, self).init()
        self.__dividerThickness = 8
        self.__collapsableSubviews = []
        return self

    def dealloc(self):
        del self.__collapsableSubviews
        super(SimpleNSSplitView, self).dealloc()

    def setDividerThickness_(self, value):
        self.__dividerThickness = value

    def dividerThickness(self):
        return self.__dividerThickness

    def setCollapsableSubviews_(self, subviews):
        self.__collapsableSubviews = subviews

    def addCollapsableSubview_(self, subview):
        self.__collapsableSubviews.append(subview)

    def collapsableSubViews(self):
        return self.__collapsableSubviews

    # draw divider

    def drawDividerInRect_(self, rect):
        if self.dividerThickness() > 2:
            super(SimpleNSSplitView, self).drawDividerInRect_(rect)
        else:
            NSColor.colorWithCalibratedWhite_alpha_(0, .42).set()
            NSBezierPath.bezierPathWithRect_(rect).fill()

    # delegate

    def splitView_canCollapseSubview_(self, splitView, subview):
        return subview in splitView.collapsableSubViews()

    def splitView_shouldCollapseSubview_forDoubleClickOnDividerAtIndex_(self, splitView, subview, dividerIndex):
        return True


class SplitView(VanillaBaseObject):

    nsSplitView = SimpleNSSplitView

    dividerStyleDict = dict(thick=NSSplitViewDividerStyleThick, thin=NSSplitViewDividerStyleThin)

    def __init__(self, posSize,
                    paneDescriptions=list(),
                    isVertical=True,
                    dividerStyle="thick",
                    dividerThickness=8,
                    autoSaveName=None):

        self._setupView(self.nsSplitView, posSize)
        self._nsObject.setVertical_(isVertical)
        self._nsObject.setDividerStyle_(self.dividerStyleDict.get(dividerStyle, "thick"))
        self._nsObject.setDividerThickness_(dividerThickness)

        self._nsObject.setDelegate_(self._nsObject)

        if autoSaveName is not None:
            self._nsObject.setAutosaveName_(autoSaveName)

        self._paneIndentifiers = dict()
        for index, paneDescription in enumerate(paneDescriptions):
            vanillaView = paneDescription.get("view")
            view = vanillaView._nsObject
            self._paneIndentifiers[paneDescription["identifier"]] = view
            self._nsObject.addSubview_(view)

            if paneDescription.get("canCollapse", True):
                self._nsObject.addCollapsableSubview_(view)

    def getNSSplitView(self):
        return self._nsObject

    def setDividerPosition(self, index, position):
        self._nsObject.setPosition_ofDividerAtIndex_(position, index)

    def isPaneVisible(self, identifier):
        view = self._paneIndentifiers[identifier]
        (x, y), (w, h) = view.frame()
        if w == 0 or h == 0:
            if self._nsObject.isVertical():
                return w != 0
            return h != 0
        return not self._nsObject.isSubviewCollapsed_(view)
