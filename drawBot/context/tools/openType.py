import AppKit
import CoreText

from fontTools.ttLib import TTFont

from drawBot.misc import memoize


def getFeatureTagsForFontAttributes(attributes):
    featureTags = list()
    for attribute in attributes:
        tag = attribute.get("CTFeatureOpenTypeTag")
        if tag:
            featureTags.append(tag)
    return featureTags


@memoize
def getFeatureTagsForFontName(fontName):
    featureTags = []
    font = AppKit.NSFont.fontWithName_size_(fontName, 12)
    if font is None:
        return featureTags
    fontDescriptor = font.fontDescriptor()
    url = CoreText.CTFontDescriptorCopyAttribute(fontDescriptor, CoreText.kCTFontURLAttribute)
    if url is None:
        return featureTags
    ft = TTFont(url.path(), lazy=True, fontNumber=0)
    featureTags = set()
    if "GPOS" in ft:
        for record in ft["GPOS"].table.FeatureList.FeatureRecord:
            featureTags.add(record.FeatureTag)
    if "GSUB" in ft:
        for record in ft["GSUB"].table.FeatureList.FeatureRecord:
            featureTags.add(record.FeatureTag)
    return list(sorted(featureTags))
