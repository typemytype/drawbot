from xml.etree.ElementTree import Element
from svgPathPen import SVGPathPen
from tools import valueToString

def writeMissingGlyph(font, svgFont):
    svgMissingGlyphAttrib = {}
    if ".notdef" in font:
        glyph = font[".notdef"]
        _writeHorizAdvX(glyph, svgMissingGlyphAttrib)
        _writeD(glyph, svgMissingGlyphAttrib)
    else:
        svgMissingGlyphAttrib = _writeDefaultMissingGlyphAttrib(font)
    svgMissingGlyph = Element("missing-glyph", attrib=svgMissingGlyphAttrib)
    svgFont.append(svgMissingGlyph)

def writeGlyph(glyph, svgFont):
    svgGlyphAttrib = {}
    _writeGlyphName(glyph, svgGlyphAttrib)
    _writeHorizAdvX(glyph, svgGlyphAttrib)
    _writeUnicode(glyph, svgGlyphAttrib)
    _writeD(glyph, svgGlyphAttrib)
    svgGlyph = Element("glyph", attrib=svgGlyphAttrib)
    svgFont.append(svgGlyph)

def _writeDefaultMissingGlyphAttrib(font):
    """
    >>> from defcon import Font
    >>> font = Font()
    >>> _writeDefaultMissingGlyphAttrib(font)
    {'horiz-adv-x': '500'}
    >>> font.info.unitsPerEm = 2048
    >>> _writeDefaultMissingGlyphAttrib(font)
    {'horiz-adv-x': '1024'}
    >>> font.info.postscriptDefaultWidthX = 250
    >>> _writeDefaultMissingGlyphAttrib(font)
    {'horiz-adv-x': '250'}
    """
    if font.info.postscriptDefaultWidthX is not None:
        width = font.info.postscriptDefaultWidthX
    elif not font.info.unitsPerEm:
        width = 500
    else:
        width = int(font.info.unitsPerEm * .5)
    return {"horiz-adv-x" : valueToString(width)}

def _writeGlyphName(glyph, attrib):
    """
    >>> from defcon import Glyph
    >>> attrib = {}
    >>> glyph = Glyph()
    >>> glyph.name = "foo"
    >>> _writeGlyphName(glyph, attrib)
    >>> attrib
    {'glyph-name': 'foo'}
    """
    assert glyph.name is not None
    attrib["glyph-name"] = glyph.name

def _writeHorizAdvX(glyph, attrib):
    """
    >>> from defcon import Glyph
    >>> attrib = {}
    >>> glyph = Glyph()
    >>> glyph.width = 100
    >>> _writeHorizAdvX(glyph, attrib)
    >>> attrib
    {'horiz-adv-x': '100'}
    """
    assert glyph.width >= 0
    attrib["horiz-adv-x"] = valueToString(glyph.width)

def _writeUnicode(glyph, attrib):
    """
    >>> from defcon import Glyph
    >>> attrib = {}
    >>> glyph = Glyph()
    >>> _writeUnicode(glyph, attrib)
    >>> attrib
    {}
    >>> glyph.unicode = ord(u"A")
    >>> _writeUnicode(glyph, attrib)
    >>> attrib
    {'unicode': u'A'}
    """
    if glyph.unicode:
        attrib["unicode"] = unichr(glyph.unicode)

def _writeD(glyph, attrib):
    """
    >>> from defcon import Glyph
    >>> attrib = {}
    >>> glyph = Glyph()
    >>> _writeD(glyph, attrib)
    >>> attrib
    {}
    >>> pen = glyph.getPen()
    >>> pen.moveTo((-10, -10))
    >>> pen.lineTo((-10, 10))
    >>> pen.lineTo((10, 10))
    >>> pen.lineTo((10, -10))
    >>> pen.closePath()
    >>> _writeD(glyph, attrib)
    >>> attrib
    {'d': 'M-10 -10V10H10V-10Z'}
    """
    pen = SVGPathPen(glyph.getParent())
    glyph.draw(pen)
    pathCommands = pen.getCommands()
    if pathCommands:
        attrib["d"] = pathCommands

if __name__ == "__main__":
    import doctest
    doctest.testmod()