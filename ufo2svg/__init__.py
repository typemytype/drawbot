import os
import gzip
import tempfile
from cStringIO import StringIO
from xml.etree.ElementTree import ElementTree, Element
from fontFace import writeFontFace
from glyphs import writeMissingGlyph, writeGlyph
from kerning import writeHKernElements

def convertUFOToSVGFont(font, destinationPathOrFile=None, doKerning=True, ignoreGlyphs=[], compress=False, whitespace=None):
    """
    Convert a UFO to a SVG font format file.
    The resulting SVG font should always be validated for standards compliance.

    font-A loaded UFO font object.
    destinationPathOrFile-A path or file object indicating where the SVG should go.
    doKerning-Boolean indicating if kerning should be written or not.
    ignoreGlyphs-A list of glyphs in the UFO that should not be written into the UFO.
    compress-Boolean indicating if the SVG should be compressed with gzip.
    whitespace-A string of whitespace to use for pretty printing the XML.
    """
    svg = Element("svg", attrib=dict(version="1.1", xmlns="http://www.w3.org/2000/svg"))
    svgDefs = Element("defs")
    svg.append(svgDefs)
    # start the font
    svgFont = Element("font", attrib={"id" : "font", "horiz-adv-x" : "0"})
    svgDefs.append(svgFont)
    # handle the font-face
    writeFontFace(font, svgFont)
    # handle the missing-glyph
    writeMissingGlyph(font, svgFont)
    # handle the glyphs
    for glyphName in sorted(font.keys()):
        if glyphName == ".notdef" or glyphName in ignoreGlyphs:
            continue
        glyph = font[glyphName]
        writeGlyph(glyph, svgFont)
    # handle the kerning
    if doKerning:
        writeHKernElements(font, svgFont, ignoreGlyphs=ignoreGlyphs)
    # indent
    if whitespace is not None:
        _indent(svg, whitespace)
    # write
    temp = StringIO()
    h = header
    if not whitespace:
        h = "".join(h.strip().splitlines())
    temp.write(h)
    tree = ElementTree(svg)
    tree.write(temp)
    data = temp.getvalue()
    temp.close()
    # compress
    if compress:
        # make a temp file
        tempPath = tempfile.mkstemp()[1]
        # gzip
        f = gzip.open(tempPath, "wb")
        f.write(data)
        f.close()
        # read the compressed data
        f = open(tempPath, "rb")
        data = f.read()
        f.close()
        # remove the temp file
        os.remove(tempPath)
    # write the result
    if isinstance(destinationPathOrFile, basestring):
        f = open(destinationPathOrFile, "wb")
        f.write(data)
        f.close()
    else:
        destinationPathOrFile.write(data)

header = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" >
"""

def _indent(elem, whitespace="    ", level=0):
    # taken from http://effbot.org/zone/element-lib.htm#prettyprint
    i = "\n" + level * whitespace
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + whitespace
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, whitespace, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
