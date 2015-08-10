from xml.etree.ElementTree import Element
from tools import valueToString

def writeFontFace(font, svgFont):
    svgFontFaceAttrib = {}
    _writeFontFamily(font, svgFontFaceAttrib)
    _writeFontStyle(font, svgFontFaceAttrib)
    _writeFontWeight(font, svgFontFaceAttrib)
    _writeFontStretch(font, svgFontFaceAttrib)
    _writeUnitsPerEm(font, svgFontFaceAttrib)
    _writeCapHeight(font, svgFontFaceAttrib)
    _writeXHeight(font, svgFontFaceAttrib)
    _writeAscent(font, svgFontFaceAttrib)
    _writeDescent(font, svgFontFaceAttrib)
    _writeBbox(font, svgFontFaceAttrib)
    svgFontFace = Element("font-face", attrib=svgFontFaceAttrib)
    svgFont.append(svgFontFace)

def _writeFontFamily(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeFontFamily(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.familyName = "Test Family"
    >>> _writeFontFamily(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'font-family': 'Test Family'}
    """
    if font.info.familyName is not None:
        svgFontFaceAttrib["font-family"] = font.info.familyName

def _writeFontStyle(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeFontStyle(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.styleMapStyleName = "regular"
    >>> _writeFontStyle(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'font-style': 'normal'}
    >>> font.info.styleMapStyleName = "italic"
    >>> _writeFontStyle(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'font-style': 'italic'}
    """
    if font.info.styleMapStyleName is not None:
        if "italic" in font.info.styleMapStyleName:
            svgFontFaceAttrib["font-style"] = "italic"
        else:
            svgFontFaceAttrib["font-style"] = "normal"

def _writeFontWeight(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeFontWeight(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.openTypeOS2WeightClass = 100
    >>> _writeFontWeight(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'font-weight': '100'}
    """
    if font.info.openTypeOS2WeightClass is not None:
        svgFontFaceAttrib["font-weight"] = valueToString(font.info.openTypeOS2WeightClass)

def _writeFontStretch(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeFontStretch(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.openTypeOS2WidthClass = 1
    >>> _writeFontStretch(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'font-stretch': 'ultra-condensed'}
    >>> font.info.openTypeOS2WidthClass = 9
    >>> _writeFontStretch(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'font-stretch': 'ultra-expanded'}
    """
    if font.info.openTypeOS2WidthClass >= 1 and font.info.openTypeOS2WidthClass <= 9:
        options = "ultra-condensed extra-condensed condensed semi-condensed normal semi-expanded expanded extra-expanded ultra-expanded".split(" ")
        svgFontFaceAttrib["font-stretch"] = options[font.info.openTypeOS2WidthClass - 1]

def _writeUnitsPerEm(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeUnitsPerEm(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.unitsPerEm = 1000
    >>> _writeUnitsPerEm(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'units-per-em': '1000'}
    """
    if font.info.unitsPerEm is not None:
        svgFontFaceAttrib["units-per-em"] = valueToString(font.info.unitsPerEm)

def _writeCapHeight(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeCapHeight(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.capHeight = 750
    >>> _writeCapHeight(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'cap-height': '750'}
    """
    if font.info.capHeight is not None:
        svgFontFaceAttrib["cap-height"] = valueToString(font.info.capHeight)

def _writeXHeight(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeXHeight(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.xHeight = 400
    >>> _writeXHeight(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'x-height': '400'}
    """
    if font.info.xHeight is not None:
        svgFontFaceAttrib["x-height"] = valueToString(font.info.xHeight)

def _writeAscent(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeAscent(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.ascender = 750
    >>> _writeAscent(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'ascent': '750'}
    """
    if font.info.ascender is not None:
        svgFontFaceAttrib["ascent"] = valueToString(font.info.ascender)

def _writeDescent(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeDescent(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {}
    >>> font.info.descender = -250
    >>> _writeDescent(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'descent': '-250'}
    """
    if font.info.descender is not None:
        svgFontFaceAttrib["descent"] = valueToString(font.info.descender)

def _writeBbox(font, svgFontFaceAttrib):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> svgFontFaceAttrib = {}
    >>> _writeBbox(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'bbox': '0 0 0 0'}
    >>> font.newGlyph("A")
    >>> glyph = font["A"]
    >>> pen = glyph.getPen()
    >>> pen.moveTo((-10, -10))
    >>> pen.lineTo((-10, 10))
    >>> pen.lineTo((10, 10))
    >>> pen.lineTo((10, -10))
    >>> pen.closePath()
    >>> _writeBbox(font, svgFontFaceAttrib)
    >>> svgFontFaceAttrib
    {'bbox': '-10 -10 10 10'}
    """
    rect = font.bounds
    if rect is None:
        rect = (0, 0, 0, 0)
    rect = [valueToString(i) for i in rect]
    svgFontFaceAttrib["bbox"] = " ".join(rect)

if __name__ == "__main__":
    import doctest
    doctest.testmod()