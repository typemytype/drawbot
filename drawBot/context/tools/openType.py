import CoreText

# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM09/AppendixF.html

_featureMap = dict(

        # Ligatures
        rlig = (1, 0),
        rlig_off = (1, 1),

        liga = (1, 2),
        liga_off = (1, 3),

        dlig = (1, 4),
        dlig_off = (1, 5),

        clig = (1, 18),
        clig_off = (1, 19),

        # Letter Case (letter case is deprecated see link above)
        _smcp = (3, 3),

        # Number Spacing
        tnum = (6, 0),
        pnum = (6, 1),

        # Number Case
        onum = (21, 0),
        lnum = (21, 1),

        # Vertical Position

        sups = (10, 1),
        subs = (10, 2),
        ordn = (10, 3),
        #dnom = (10, 2), ??
        #numr = (10, 3), ??
        sinf = (10, 4),

        # Fractions
        frac = (11, 2),

        # Style Options
        titl = (19, 4),

        # Case Sensitive Layout
        case = (33, 0),
        case_off = (33, 1),
        cpsp = (33, 2),
        cpsp_off = (33, 3),

        # Stylistic Alternatives
        ss01 = (35, 2),
        ss01_off = (35, 3),
        ss02 = (35, 4),
        ss02_off = (35, 5),
        ss03 = (35, 6),
        ss03_off = (35, 7),
        ss04 = (35, 8),
        ss04_off = (35, 9),
        ss05 = (35, 10),
        ss05_off = (35, 11),
        ss06 = (35, 12),
        ss06_off = (35, 13),
        ss07 = (35, 14),
        ss07_off = (35, 15),
        ss08 = (35, 16),
        ss08_off = (35, 17),
        ss09 = (35, 18),
        ss09_off = (35, 19),
        ss10 = (35, 20),
        ss10_off = (35, 21),
        ss11 = (35, 22),
        ss11_off = (35, 23),
        ss12 = (35, 24),
        ss12_off = (35, 25),
        ss13 = (35, 26),
        ss13_off = (35, 27),
        ss14 = (35, 28),
        ss14_off = (35, 29),
        ss15 = (35, 30),
        ss15_off = (35, 31),
        ss16 = (35, 32),
        ss16_off = (35, 33),
        ss17 = (35, 34),
        ss17_off = (35, 35),
        ss18 = (35, 36),
        ss18_off = (35, 37),
        ss19 = (35, 38),
        ss19_off = (35, 39),
        ss20 = (35, 40),
        ss20_off = (35, 41),

        # Contextual Alternates
        calt = (36, 0),
        calt_off = (36, 1),
        swsh = (36, 2),
        swsh_off = (36, 3),
        cswh = (36, 4),
        cswh_off = (36, 5),

        # Lower Case
        smcp = (37, 1),
        pcap = (37, 2),

        # Upper Case
        c2sc = (38, 1),
        c2pc = (38, 2),

    )

featureMap = dict()
reversedFeatureMap = dict()

for key, value in _featureMap.items():
    
    featureType, featureSelector = value
    feature = {
        CoreText.NSFontFeatureTypeIdentifierKey : featureType,
        CoreText.NSFontFeatureSelectorIdentifierKey : featureSelector
    }
    featureMap[key] = feature
    reversedFeatureMap[(featureType, featureSelector)] = key


def getFeatureTagsForFontName(fontName):
    descriptor = CoreText.NSFontDescriptor.fontDescriptorWithName_size_(fontName, 12)
    featureDescriptions = CoreText.CTFontDescriptorCopyAttribute(descriptor, CoreText.kCTFontFeaturesAttribute)
    if featureDescriptions is None:
        return []
    featureTags = list()
    for featureDescription in featureDescriptions:
        featureType = featureDescription[CoreText.NSFontFeatureTypeIdentifierKey]
        for selector in featureDescription["CTFeatureTypeSelectors"]:
            featureSelector = selector[CoreText.NSFontFeatureSelectorIdentifierKey]
            featureTag = reversedFeatureMap.get((featureType, featureSelector))
            if featureTag:
                featureTag = featureTag.replace("_off", "")
                if featureTag not in featureTags:
                    featureTags.append(featureTag)
    return featureTags
