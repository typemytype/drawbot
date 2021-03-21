import os
import AppKit
import CoreText

from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
from fontTools.misc.macCreatorType import getMacCreatorAndType
from fontTools.misc.macRes import ResourceReader

from drawBot.misc import memoize
from . import SFNTLayoutTypes


def getFeatureTagsForFontAttributes(attributes):
    featureTags = dict()
    for attribute in attributes:
        tag = attribute.get("CTFeatureOpenTypeTag")
        if tag is not None:
            featureTags[tag] = attribute.get("CTFeatureOpenTypeValue", True)
        else:
            # Fallback for macOS < 10.13
            featureType = attribute.get("CTFeatureTypeIdentifier")
            featureSelector = attribute.get("CTFeatureSelectorIdentifier")
            tag = SFNTLayoutTypes.reversedFeatureMap[(featureType, featureSelector)]
            value = True
            if len(tag) == 8 and tag.endswith("_off"):
                value = False
                tag = tag[:4]
            featureTags[tag] = value
    return featureTags


@memoize
def getFeatureTagsForFont(font):
    featureTags = []
    if font is None:
        return featureTags
    fontDescriptor = font.fontDescriptor()
    url = CoreText.CTFontDescriptorCopyAttribute(fontDescriptor, CoreText.kCTFontURLAttribute)
    psFontName = CoreText.CTFontDescriptorCopyAttribute(fontDescriptor, CoreText.kCTFontNameAttribute)
    if url is None or psFontName is None:
        return featureTags
    path = url.path()
    ext = os.path.splitext(path)[1].lower()
    macType = getMacCreatorAndType(path)[1]
    if ext in (".ttc", ".otc"):
        ft = _getTTFontFromTTC(path, psFontName)
    elif ext in (".ttf", ".otf"):
        ft = TTFont(path, lazy=True)
    elif ext == ".dfont" or macType == "FFIL":
        ft = _getTTFontFromSuitcase(path, psFontName)
        if ft is None:
            return featureTags
    else:
        return featureTags
    featureTags = set()
    if "GPOS" in ft and ft["GPOS"].table.FeatureList is not None:
        for record in ft["GPOS"].table.FeatureList.FeatureRecord:
            featureTags.add(record.FeatureTag)
    if "GSUB" in ft and ft["GSUB"].table.FeatureList is not None:
        for record in ft["GSUB"].table.FeatureList.FeatureRecord:
            featureTags.add(record.FeatureTag)
    if "feat" in ft:
        for featureName in ft["feat"].table.FeatureNames.FeatureName:
            for featureSetting in featureName.Settings.Setting:
                featureTag = SFNTLayoutTypes.reversedFeatureMap.get((featureName.FeatureType, featureSetting.SettingValue))
                if featureTag:
                    featureTag = featureTag.replace("_off", "")
                    featureTags.add(featureTag)
    ft.close()
    return list(sorted(featureTags))


def _getTTFontFromSuitcase(path, psFontName, searchOrder=((1, 0), (3, 1))):
    # Support for .dfont and especially "regular" suitcases is minimal,
    # and we will not raise an error when the requested font isn't found,
    # but will return None.
    rr = ResourceReader(path)
    if "sfnt" not in rr:
        return None
    for index in rr.getIndices("sfnt"):
        font = TTFont(path, lazy=True, res_name_or_index=index)
        for platID, platEncID in searchOrder:
            nameRecord = font["name"].getName(6, platID, platEncID)
            if nameRecord is not None and str(nameRecord) == psFontName:
                return font
    return None


def _getTTFontFromTTC(path, psFontName, searchOrder=((1, 0), (3, 1))):
    ttc = TTCollection(path, lazy=True)
    for font in ttc:
        for platID, platEncID in searchOrder:
            nameRecord = font["name"].getName(6, platID, platEncID)
            if nameRecord is not None and str(nameRecord) == psFontName:
                return font
    raise IndexError(f"font {psFontName} not found")
