import os
import AppKit
import CoreText

from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection

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
def getFeatureTagsForFontName(fontName):
    featureTags = []
    font = AppKit.NSFont.fontWithName_size_(fontName, 12)
    if font is None:
        return featureTags
    fontDescriptor = font.fontDescriptor()
    url = CoreText.CTFontDescriptorCopyAttribute(fontDescriptor, CoreText.kCTFontURLAttribute)
    psFontName = CoreText.CTFontDescriptorCopyAttribute(fontDescriptor, CoreText.kCTFontNameAttribute)
    if url is None or psFontName is None:
        return featureTags
    path = url.path()
    ext = os.path.splitext(path)[1].lower()
    if ext in (".ttc", ".otc"):
        ft = _getTTFontFromTTC(path, psFontName)
    elif ext == ".dfont":
        ft = TTFont(path, lazy=True, res_name_or_index=psFontName)
    else:
        ft = TTFont(path, lazy=True)
    featureTags = set()
    if "GPOS" in ft:
        for record in ft["GPOS"].table.FeatureList.FeatureRecord:
            featureTags.add(record.FeatureTag)
    if "GSUB" in ft:
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


def _getTTFontFromTTC(path, psFontName, searchOrder=((1, 0), (3, 1))):
    ttc = TTCollection(path, lazy=True)
    for font in ttc:
        for platID, platEncID in searchOrder:
            nameRecord = font["name"].getName(6, platID, platEncID)
            if nameRecord is not None and str(nameRecord) == psFontName:
                return font
    raise IndexError(f"font {psFontName} not found")
