from collections import OrderedDict

import CoreText
from fontTools.ttLib import TTFont

from drawBot.misc import memoize, warnings

"""
https://developer.apple.com/documentation/coretext/ctfont/font_variation_axis_dictionary_keys?language=objc
https://developer.apple.com/documentation/coretext/1508650-ctfontdescriptorcreatecopywithva?language=objc
"""


def convertIntToVariationTag(value):
    chars = []
    for shift in range(4):
        chars.append(chr((value >> (shift * 8)) & 0xFF))
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
        name = variationAxesDescription.get(CoreText.kCTFontVariationAxisNameKey, tag)
        minValue = variationAxesDescription[CoreText.kCTFontVariationAxisMinimumValueKey]
        maxValue = variationAxesDescription[CoreText.kCTFontVariationAxisMaximumValueKey]
        defaultValue = variationAxesDescription[CoreText.kCTFontVariationAxisDefaultValueKey]
        data = dict(name=name, minValue=minValue, maxValue=maxValue, defaultValue=defaultValue)
        axes[tag] = data
    return axes


@memoize
def getNamedInstancesForDescriptors(descriptors):
    """
    Return a dict { postscriptName: location } of all named instances in a given font.
    """
    instances = dict()

    for descriptor in descriptors:
        # convert to a ctFont
        font = CoreText.CTFontCreateWithFontDescriptor(descriptor, 10, None)
        # get the default variation axes
        variationAxesDescriptions = CoreText.CTFontCopyVariationAxes(font)

        if variationAxesDescriptions is not None:
            # variable fonts have named instances
            fontVariation = CoreText.CTFontCopyVariation(font)
            variationCoordinates = {}

            for variationAxesDescription in variationAxesDescriptions:
                tag = convertIntToVariationTag(variationAxesDescription[CoreText.NSFontVariationAxisIdentifierKey])
                variationCoordinates[tag] = variationAxesDescription[CoreText.NSFontVariationAxisDefaultValueKey]

            for fontVariationKey, fontVariationValue in fontVariation.items():
                tag = convertIntToVariationTag(fontVariationKey)
                variationCoordinates[tag] = fontVariationValue

            instances[descriptor.postscriptName()] = variationCoordinates

    return instances


def getFontVariationAttributes(font, fontVariations):
    coreTextFontVariations = dict()
    axes = getVariationAxesForFont(font)

    for axisTag, axis in axes.items():
        value = min(
            max(fontVariations.get(axisTag, axis["defaultValue"]), axis["minValue"]),
            axis["maxValue"],
        )
        coreTextFontVariations[convertVariationTagToInt(axisTag)] = value

    for axisTag in sorted(set(fontVariations) - set(axes)):
        warnings.warn("variation axis '%s' not available for '%s'" % (axisTag, font.fontName()))

    return coreTextFontVariations
