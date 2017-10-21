import CoreText
from collections import OrderedDict

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


def getVariationAxesForFontName(fontName):
    axes = OrderedDict()
    font = CoreText.CTFontCreateWithName(fontName, 12, None)
    variationAxesDescriptions = CoreText.CTFontCopyVariationAxes(font)
    if variationAxesDescriptions is None:
        # 'normal' fonts have no axes descriptions
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
