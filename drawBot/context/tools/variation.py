import CoreText
from collections import OrderedDict

from fontTools.ttLib import TTFont

from drawBot.misc import memoize, warnings

"""
https://developer.apple.com/documentation/coretext/ctfont/font_variation_axis_dictionary_keys?language=objc
https://developer.apple.com/documentation/coretext/1508650-ctfontdescriptorcreatecopywithva?language=objc
"""


def convertIntToVariationTag(value):
    chars = []
    for shift in range(4):
        chars.append(chr((value >> (shift * 8)) & 0xff))
    return "".join(reversed(chars))


def convertVariationTagToInt(tag):
    assert len(tag) == 4
    i = 0
    for c in tag:
        i <<= 8
        i |= ord(c)
    return i


@memoize
def getVariationAxesForFont(font):
    """
    Return a dictionary { axis tag: { name: , minValue: , maxValue: } }
    """
    axes = OrderedDict()
    variationAxesDescriptions = CoreText.CTFontCopyVariationAxes(font)
    if variationAxesDescriptions is None:
        # non-variable fonts have no axes descriptions
        return axes
    for variationAxesDescription in variationAxesDescriptions:
        tag = convertIntToVariationTag(variationAxesDescription[CoreText.kCTFontVariationAxisIdentifierKey])
        name = variationAxesDescription[CoreText.kCTFontVariationAxisNameKey]
        minValue = variationAxesDescription[CoreText.kCTFontVariationAxisMinimumValueKey]
        maxValue = variationAxesDescription[CoreText.kCTFontVariationAxisMaximumValueKey]
        defaultValue = variationAxesDescription[CoreText.kCTFontVariationAxisDefaultValueKey]
        data = dict(name=name, minValue=minValue, maxValue=maxValue, defaultValue=defaultValue)
        axes[tag] = data
    return axes


@memoize
def getNamedInstancesForFont(font):
    """
    Return a dict { postscriptName: location } of all named instances in a given font.
    """
    instances = OrderedDict()
    if font is None:
        return instances
    fontDescriptor = font.fontDescriptor()
    url = CoreText.CTFontDescriptorCopyAttribute(fontDescriptor, CoreText.kCTFontURLAttribute)
    if url is None:
        return instances

    variationAxesDescriptions = CoreText.CTFontCopyVariationAxes(font)
    if variationAxesDescriptions is None:
        # non-variable fonts have no named instances
        return instances
    tagNameMap = {}
    for variationAxesDescription in variationAxesDescriptions:
        tag = convertIntToVariationTag(variationAxesDescription[CoreText.kCTFontVariationAxisIdentifierKey])
        name = variationAxesDescription[CoreText.kCTFontVariationAxisNameKey]
        tagNameMap[tag] = name

    ft = TTFont(url.path(), lazy=True, fontNumber=0)
    if "fvar" in ft:
        cgFont, _ = CoreText.CTFontCopyGraphicsFont(font, None)
        fvar = ft["fvar"]

        for instance in fvar.instances:
            fontVariations = dict()
            for axis, value in instance.coordinates.items():
                fontVariations[tagNameMap[axis]] = value

            varFont = CoreText.CGFontCreateCopyWithVariations(cgFont, fontVariations)
            postScriptName = CoreText.CGFontCopyPostScriptName(varFont)
            instances[postScriptName] = instance.coordinates

    ft.close()
    return instances


def getFontVariationAttributes(font, fontVariations):
    coreTextFontVariations = dict()
    if fontVariations:
        existingAxes = getVariationAxesForFont(font)
        for axis, value in fontVariations.items():
            if axis in existingAxes:
                existinsAxis = existingAxes[axis]
                # clip variation value within the min max value
                if value < existinsAxis["minValue"]:
                    value = existinsAxis["minValue"]
                if value > existinsAxis["maxValue"]:
                    value = existinsAxis["maxValue"]
                coreTextFontVariations[convertVariationTagToInt(axis)] = value
            else:
                warnings.warn("variation axis '%s' not available for '%s'" % (axis, font.fontName()))
    return coreTextFontVariations
