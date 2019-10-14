import CoreText

# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM09/AppendixF.html
# https://github.com/behdad/harfbuzz/blob/master/src/hb-coretext.cc#L381

# as taken from SFNTLayoutTypes.h

# Feature types
kAllTypographicFeaturesType = 0
kLigaturesType  = 1
kCursiveConnectionType = 2
kLetterCaseType  = 3 # deprecated - use kLowerCaseType or kUpperCaseType instead
kVerticalSubstitutionType = 4
kLinguisticRearrangementType = 5
kNumberSpacingType  = 6
kSmartSwashType  = 8
kDiacriticsType  = 9
kVerticalPositionType  = 10
kFractionsType  = 11
kOverlappingCharactersType = 13
kTypographicExtrasType = 14
kMathematicalExtrasType = 15
kOrnamentSetsType  = 16
kCharacterAlternativesType = 17
kDesignComplexityType  = 18
kStyleOptionsType  = 19
kCharacterShapeType  = 20
kNumberCaseType  = 21
kTextSpacingType  = 22
kTransliterationType  = 23
kAnnotationType  = 24
kKanaSpacingType  = 25
kIdeographicSpacingType = 26
kUnicodeDecompositionType = 27
kRubyKanaType   = 28
kCJKSymbolAlternativesType = 29
kIdeographicAlternativesType = 30
kCJKVerticalRomanPlacementType = 31
kItalicCJKRomanType  = 32
kCaseSensitiveLayoutType = 33
kAlternateKanaType  = 34
kStylisticAlternativesType = 35
kContextualAlternatesType = 36
kLowerCaseType  = 37
kUpperCaseType  = 38
kLanguageTagType  = 39
kCJKRomanSpacingType  = 103
kLastFeatureType  = -1

# Selectors for feature type kAllTypographicFeaturesType
kAllTypeFeaturesOnSelector = 0
kAllTypeFeaturesOffSelector = 1

# Selectors for feature type kLigaturesType
kRequiredLigaturesOnSelector = 0
kRequiredLigaturesOffSelector = 1
kCommonLigaturesOnSelector = 2
kCommonLigaturesOffSelector = 3
kRareLigaturesOnSelector = 4
kRareLigaturesOffSelector = 5
kLogosOnSelector = 6
kLogosOffSelector = 7
kRebusPicturesOnSelector = 8
kRebusPicturesOffSelector = 9
kDiphthongLigaturesOnSelector = 10
kDiphthongLigaturesOffSelector = 11
kSquaredLigaturesOnSelector = 12
kSquaredLigaturesOffSelector = 13
kAbbrevSquaredLigaturesOnSelector = 14
kAbbrevSquaredLigaturesOffSelector = 15
kSymbolLigaturesOnSelector = 16
kSymbolLigaturesOffSelector = 17
kContextualLigaturesOnSelector = 18
kContextualLigaturesOffSelector = 19
kHistoricalLigaturesOnSelector = 20
kHistoricalLigaturesOffSelector = 21

# Selectors for feature type kCursiveConnectionType
kUnconnectedSelector  = 0
kPartiallyConnectedSelector = 1
kCursiveSelector  = 2

# Selectors for feature type kLetterCaseType
kUpperAndLowerCaseSelector = 0 # deprecated
kAllCapsSelector  = 1 # deprecated
kAllLowerCaseSelector  = 2 # deprecated
kSmallCapsSelector  = 3 # deprecated
kInitialCapsSelector  = 4 # deprecated
kInitialCapsAndSmallCapsSelector = 5 # deprecated

# Selectors for feature type kVerticalSubstitutionType
kSubstituteVerticalFormsOnSelector = 0
kSubstituteVerticalFormsOffSelector = 1

# Selectors for feature type kLinguisticRearrangementType
kLinguisticRearrangementOnSelector = 0
kLinguisticRearrangementOffSelector = 1

# Selectors for feature type kNumberSpacingType
kMonospacedNumbersSelector = 0
kProportionalNumbersSelector = 1
kThirdWidthNumbersSelector = 2
kQuarterWidthNumbersSelector = 3

# Selectors for feature type kSmartSwashType
kWordInitialSwashesOnSelector = 0
kWordInitialSwashesOffSelector = 1
kWordFinalSwashesOnSelector = 2
kWordFinalSwashesOffSelector = 3
kLineInitialSwashesOnSelector = 4
kLineInitialSwashesOffSelector = 5
kLineFinalSwashesOnSelector = 6
kLineFinalSwashesOffSelector = 7
kNonFinalSwashesOnSelector = 8
kNonFinalSwashesOffSelector = 9

# Selectors for feature type kDiacriticsType
kShowDiacriticsSelector = 0
kHideDiacriticsSelector = 1
kDecomposeDiacriticsSelector = 2

# Selectors for feature type kVerticalPositionType
kNormalPositionSelector = 0
kSuperiorsSelector  = 1
kInferiorsSelector  = 2
kOrdinalsSelector  = 3
kScientificInferiorsSelector = 4

# Selectors for feature type kFractionsType
kNoFractionsSelector  = 0
kVerticalFractionsSelector = 1
kDiagonalFractionsSelector = 2

# Selectors for feature type kOverlappingCharactersType
kPreventOverlapOnSelector = 0
kPreventOverlapOffSelector = 1

# Selectors for feature type kTypographicExtrasType
kHyphensToEmDashOnSelector = 0
kHyphensToEmDashOffSelector = 1
kHyphenToEnDashOnSelector = 2
kHyphenToEnDashOffSelector = 3
kSlashedZeroOnSelector = 4
kSlashedZeroOffSelector = 5
kFormInterrobangOnSelector = 6
kFormInterrobangOffSelector = 7
kSmartQuotesOnSelector = 8
kSmartQuotesOffSelector = 9
kPeriodsToEllipsisOnSelector = 10
kPeriodsToEllipsisOffSelector = 11

# Selectors for feature type kMathematicalExtrasType
kHyphenToMinusOnSelector = 0
kHyphenToMinusOffSelector = 1
kAsteriskToMultiplyOnSelector = 2
kAsteriskToMultiplyOffSelector = 3
kSlashToDivideOnSelector = 4
kSlashToDivideOffSelector = 5
kInequalityLigaturesOnSelector = 6
kInequalityLigaturesOffSelector = 7
kExponentsOnSelector  = 8
kExponentsOffSelector  = 9
kMathematicalGreekOnSelector = 10
kMathematicalGreekOffSelector = 11

# Selectors for feature type kOrnamentSetsType
kNoOrnamentsSelector  = 0
kDingbatsSelector  = 1
kPiCharactersSelector  = 2
kFleuronsSelector  = 3
kDecorativeBordersSelector = 4
kInternationalSymbolsSelector = 5
kMathSymbolsSelector  = 6

# Selectors for feature type kCharacterAlternativesType
kNoAlternatesSelector  = 0

# Selectors for feature type kDesignComplexityType
kDesignLevel1Selector  = 0
kDesignLevel2Selector  = 1
kDesignLevel3Selector  = 2
kDesignLevel4Selector  = 3
kDesignLevel5Selector  = 4

# Selectors for feature type kStyleOptionsType
kNoStyleOptionsSelector = 0
kDisplayTextSelector  = 1
kEngravedTextSelector  = 2
kIlluminatedCapsSelector = 3
kTitlingCapsSelector  = 4
kTallCapsSelector  = 5

# Selectors for feature type kCharacterShapeType
kTraditionalCharactersSelector = 0
kSimplifiedCharactersSelector = 1
kJIS1978CharactersSelector = 2
kJIS1983CharactersSelector = 3
kJIS1990CharactersSelector = 4
kTraditionalAltOneSelector = 5
kTraditionalAltTwoSelector = 6
kTraditionalAltThreeSelector = 7
kTraditionalAltFourSelector = 8
kTraditionalAltFiveSelector = 9
kExpertCharactersSelector = 10
kJIS2004CharactersSelector = 11
kHojoCharactersSelector = 12
kNLCCharactersSelector = 13
kTraditionalNamesCharactersSelector = 14

# Selectors for feature type kNumberCaseType
kLowerCaseNumbersSelector = 0
kUpperCaseNumbersSelector = 1

# Selectors for feature type kTextSpacingType
kProportionalTextSelector = 0
kMonospacedTextSelector = 1
kHalfWidthTextSelector = 2
kThirdWidthTextSelector = 3
kQuarterWidthTextSelector = 4
kAltProportionalTextSelector = 5
kAltHalfWidthTextSelector = 6

# Selectors for feature type kTransliterationType
kNoTransliterationSelector = 0
kHanjaToHangulSelector = 1
kHiraganaToKatakanaSelector = 2
kKatakanaToHiraganaSelector = 3
kKanaToRomanizationSelector = 4
kRomanizationToHiraganaSelector = 5
kRomanizationToKatakanaSelector = 6
kHanjaToHangulAltOneSelector = 7
kHanjaToHangulAltTwoSelector = 8
kHanjaToHangulAltThreeSelector = 9

# Selectors for feature type kAnnotationType
kNoAnnotationSelector  = 0
kBoxAnnotationSelector = 1
kRoundedBoxAnnotationSelector = 2
kCircleAnnotationSelector = 3
kInvertedCircleAnnotationSelector = 4
kParenthesisAnnotationSelector = 5
kPeriodAnnotationSelector = 6
kRomanNumeralAnnotationSelector = 7
kDiamondAnnotationSelector = 8
kInvertedBoxAnnotationSelector = 9
kInvertedRoundedBoxAnnotationSelector = 10

# Selectors for feature type kKanaSpacingType
kFullWidthKanaSelector = 0
kProportionalKanaSelector = 1

# Selectors for feature type kIdeographicSpacingType
kFullWidthIdeographsSelector = 0
kProportionalIdeographsSelector = 1
kHalfWidthIdeographsSelector = 2

# Selectors for feature type kUnicodeDecompositionType
kCanonicalCompositionOnSelector = 0
kCanonicalCompositionOffSelector = 1
kCompatibilityCompositionOnSelector = 2
kCompatibilityCompositionOffSelector = 3
kTranscodingCompositionOnSelector = 4
kTranscodingCompositionOffSelector = 5

# Selectors for feature type kRubyKanaType
kNoRubyKanaSelector  = 0 # deprecated - use kRubyKanaOffSelector instead
kRubyKanaSelector  = 1 # deprecated - use kRubyKanaOnSelector instead
kRubyKanaOnSelector  = 2
kRubyKanaOffSelector  = 3

# Selectors for feature type kCJKSymbolAlternativesType
kNoCJKSymbolAlternativesSelector = 0
kCJKSymbolAltOneSelector = 1
kCJKSymbolAltTwoSelector = 2
kCJKSymbolAltThreeSelector = 3
kCJKSymbolAltFourSelector = 4
kCJKSymbolAltFiveSelector = 5

# Selectors for feature type kIdeographicAlternativesType
kNoIdeographicAlternativesSelector = 0
kIdeographicAltOneSelector = 1
kIdeographicAltTwoSelector = 2
kIdeographicAltThreeSelector = 3
kIdeographicAltFourSelector = 4
kIdeographicAltFiveSelector = 5

# Selectors for feature type kCJKVerticalRomanPlacementType
kCJKVerticalRomanCenteredSelector = 0
kCJKVerticalRomanHBaselineSelector = 1

# Selectors for feature type kItalicCJKRomanType
kNoCJKItalicRomanSelector = 0 # deprecated - use kCJKItalicRomanOffSelector instead
kCJKItalicRomanSelector = 1 # deprecated - use kCJKItalicRomanOnSelector instead
kCJKItalicRomanOnSelector = 2
kCJKItalicRomanOffSelector = 3

# Selectors for feature type kCaseSensitiveLayoutType
kCaseSensitiveLayoutOnSelector = 0
kCaseSensitiveLayoutOffSelector = 1
kCaseSensitiveSpacingOnSelector = 2
kCaseSensitiveSpacingOffSelector = 3

# Selectors for feature type kAlternateKanaType
kAlternateHorizKanaOnSelector = 0
kAlternateHorizKanaOffSelector = 1
kAlternateVertKanaOnSelector = 2
kAlternateVertKanaOffSelector = 3

# Selectors for feature type kStylisticAlternativesType
kNoStylisticAlternatesSelector = 0
kStylisticAltOneOnSelector = 2
kStylisticAltOneOffSelector = 3
kStylisticAltTwoOnSelector = 4
kStylisticAltTwoOffSelector = 5
kStylisticAltThreeOnSelector = 6
kStylisticAltThreeOffSelector = 7
kStylisticAltFourOnSelector = 8
kStylisticAltFourOffSelector = 9
kStylisticAltFiveOnSelector = 10
kStylisticAltFiveOffSelector = 11
kStylisticAltSixOnSelector = 12
kStylisticAltSixOffSelector = 13
kStylisticAltSevenOnSelector = 14
kStylisticAltSevenOffSelector = 15
kStylisticAltEightOnSelector = 16
kStylisticAltEightOffSelector = 17
kStylisticAltNineOnSelector = 18
kStylisticAltNineOffSelector = 19
kStylisticAltTenOnSelector = 20
kStylisticAltTenOffSelector = 21
kStylisticAltElevenOnSelector = 22
kStylisticAltElevenOffSelector = 23
kStylisticAltTwelveOnSelector = 24
kStylisticAltTwelveOffSelector = 25
kStylisticAltThirteenOnSelector = 26
kStylisticAltThirteenOffSelector = 27
kStylisticAltFourteenOnSelector = 28
kStylisticAltFourteenOffSelector = 29
kStylisticAltFifteenOnSelector = 30
kStylisticAltFifteenOffSelector = 31
kStylisticAltSixteenOnSelector = 32
kStylisticAltSixteenOffSelector = 33
kStylisticAltSeventeenOnSelector = 34
kStylisticAltSeventeenOffSelector = 35
kStylisticAltEighteenOnSelector = 36
kStylisticAltEighteenOffSelector = 37
kStylisticAltNineteenOnSelector = 38
kStylisticAltNineteenOffSelector = 39
kStylisticAltTwentyOnSelector = 40
kStylisticAltTwentyOffSelector = 41

# Selectors for feature type kContextualAlternatesType
kContextualAlternatesOnSelector = 0
kContextualAlternatesOffSelector = 1
kSwashAlternatesOnSelector = 2
kSwashAlternatesOffSelector = 3
kContextualSwashAlternatesOnSelector = 4
kContextualSwashAlternatesOffSelector = 5

# Selectors for feature type kLowerCaseType
kDefaultLowerCaseSelector = 0
kLowerCaseSmallCapsSelector = 1
kLowerCasePetiteCapsSelector = 2

# Selectors for feature type kUpperCaseType
kDefaultUpperCaseSelector = 0
kUpperCaseSmallCapsSelector = 1
kUpperCasePetiteCapsSelector = 2

# Selectors for feature type kCJKRomanSpacingType
kHalfWidthCJKRomanSelector = 0
kProportionalCJKRomanSelector = 1
kDefaultCJKRomanSelector = 2
kFullWidthCJKRomanSelector = 3

# Table data courtesy of Apple.
_coreTextfeatureData = [
    ( 'c2pc',   kUpperCaseType,             kUpperCasePetiteCapsSelector,           kDefaultUpperCaseSelector ),
    ( 'c2sc',   kUpperCaseType,             kUpperCaseSmallCapsSelector,            kDefaultUpperCaseSelector ),
    ( 'calt',   kContextualAlternatesType,  kContextualAlternatesOnSelector,        kContextualAlternatesOffSelector ),
    ( 'case',   kCaseSensitiveLayoutType,   kCaseSensitiveLayoutOnSelector,         kCaseSensitiveLayoutOffSelector ),
    ( 'clig',   kLigaturesType,             kContextualLigaturesOnSelector,         kContextualLigaturesOffSelector ),
    ( 'cpsp',   kCaseSensitiveLayoutType,   kCaseSensitiveSpacingOnSelector,        kCaseSensitiveSpacingOffSelector ),
    ( 'cswh',   kContextualAlternatesType,  kContextualSwashAlternatesOnSelector,   kContextualSwashAlternatesOffSelector ),
    ( 'dlig',   kLigaturesType,             kRareLigaturesOnSelector,               kRareLigaturesOffSelector ),
    ( 'expt',   kCharacterShapeType,        kExpertCharactersSelector,              16 ),
    ( 'frac',   kFractionsType,             kDiagonalFractionsSelector,             kNoFractionsSelector ),
    ( 'fwid',   kTextSpacingType,           kMonospacedTextSelector,                7 ),
    ( 'halt',   kTextSpacingType,           kAltHalfWidthTextSelector,              7 ),
    ( 'hist',   kLigaturesType,             kHistoricalLigaturesOnSelector,         kHistoricalLigaturesOffSelector ),
    ( 'hkna',   kAlternateKanaType,         kAlternateHorizKanaOnSelector,          kAlternateHorizKanaOffSelector, ),
    ( 'hlig',   kLigaturesType,             kHistoricalLigaturesOnSelector,         kHistoricalLigaturesOffSelector ),
    ( 'hngl',   kTransliterationType,       kHanjaToHangulSelector,                 kNoTransliterationSelector ),
    ( 'hojo',   kCharacterShapeType,        kHojoCharactersSelector,                16 ),
    ( 'hwid',   kTextSpacingType,           kHalfWidthTextSelector,                 7 ),
    ( 'ital',   kItalicCJKRomanType,        kCJKItalicRomanOnSelector,              kCJKItalicRomanOffSelector ),
    ( 'jp04',   kCharacterShapeType,        kJIS2004CharactersSelector,             16 ),
    ( 'jp78',   kCharacterShapeType,        kJIS1978CharactersSelector,             16 ),
    ( 'jp83',   kCharacterShapeType,        kJIS1983CharactersSelector,             16 ),
    ( 'jp90',   kCharacterShapeType,        kJIS1990CharactersSelector,             16 ),
    ( 'liga',   kLigaturesType,             kCommonLigaturesOnSelector,             kCommonLigaturesOffSelector ),
    ( 'lnum',   kNumberCaseType,            kUpperCaseNumbersSelector,              2 ),
    ( 'mgrk',   kMathematicalExtrasType,    kMathematicalGreekOnSelector,           kMathematicalGreekOffSelector ),
    ( 'nlck',   kCharacterShapeType,        kNLCCharactersSelector,                 16 ),
    ( 'onum',   kNumberCaseType,            kLowerCaseNumbersSelector,              2 ),
    ( 'ordn',   kVerticalPositionType,      kOrdinalsSelector,                      kNormalPositionSelector ),
    ( 'palt',   kTextSpacingType,           kAltProportionalTextSelector,           7 ),
    ( 'pcap',   kLowerCaseType,             kLowerCasePetiteCapsSelector,           kDefaultLowerCaseSelector ),
    ( 'pkna',   kTextSpacingType,           kProportionalTextSelector,              7 ),
    ( 'pnum',   kNumberSpacingType,         kProportionalNumbersSelector,           4 ),
    ( 'pwid',   kTextSpacingType,           kProportionalTextSelector,              7 ),
    ( 'qwid',   kTextSpacingType,           kQuarterWidthTextSelector,              7 ),
    ( 'ruby',   kRubyKanaType,              kRubyKanaOnSelector,                    kRubyKanaOffSelector ),
    ( 'sinf',   kVerticalPositionType,      kScientificInferiorsSelector,           kNormalPositionSelector ),
    ( 'smcp',   kLowerCaseType,             kLowerCaseSmallCapsSelector,            kDefaultLowerCaseSelector ),
    ( 'smpl',   kCharacterShapeType,        kSimplifiedCharactersSelector,          16 ),
    ( 'ss01',   kStylisticAlternativesType, kStylisticAltOneOnSelector,             kStylisticAltOneOffSelector ),
    ( 'ss02',   kStylisticAlternativesType, kStylisticAltTwoOnSelector,             kStylisticAltTwoOffSelector ),
    ( 'ss03',   kStylisticAlternativesType, kStylisticAltThreeOnSelector,           kStylisticAltThreeOffSelector ),
    ( 'ss04',   kStylisticAlternativesType, kStylisticAltFourOnSelector,            kStylisticAltFourOffSelector ),
    ( 'ss05',   kStylisticAlternativesType, kStylisticAltFiveOnSelector,            kStylisticAltFiveOffSelector ),
    ( 'ss06',   kStylisticAlternativesType, kStylisticAltSixOnSelector,             kStylisticAltSixOffSelector ),
    ( 'ss07',   kStylisticAlternativesType, kStylisticAltSevenOnSelector,           kStylisticAltSevenOffSelector ),
    ( 'ss08',   kStylisticAlternativesType, kStylisticAltEightOnSelector,           kStylisticAltEightOffSelector ),
    ( 'ss09',   kStylisticAlternativesType, kStylisticAltNineOnSelector,            kStylisticAltNineOffSelector ),
    ( 'ss10',   kStylisticAlternativesType, kStylisticAltTenOnSelector,             kStylisticAltTenOffSelector ),
    ( 'ss11',   kStylisticAlternativesType, kStylisticAltElevenOnSelector,          kStylisticAltElevenOffSelector ),
    ( 'ss12',   kStylisticAlternativesType, kStylisticAltTwelveOnSelector,          kStylisticAltTwelveOffSelector ),
    ( 'ss13',   kStylisticAlternativesType, kStylisticAltThirteenOnSelector,        kStylisticAltThirteenOffSelector ),
    ( 'ss14',   kStylisticAlternativesType, kStylisticAltFourteenOnSelector,        kStylisticAltFourteenOffSelector ),
    ( 'ss15',   kStylisticAlternativesType, kStylisticAltFifteenOnSelector,         kStylisticAltFifteenOffSelector ),
    ( 'ss16',   kStylisticAlternativesType, kStylisticAltSixteenOnSelector,         kStylisticAltSixteenOffSelector ),
    ( 'ss17',   kStylisticAlternativesType, kStylisticAltSeventeenOnSelector,       kStylisticAltSeventeenOffSelector ),
    ( 'ss18',   kStylisticAlternativesType, kStylisticAltEighteenOnSelector,        kStylisticAltEighteenOffSelector ),
    ( 'ss19',   kStylisticAlternativesType, kStylisticAltNineteenOnSelector,        kStylisticAltNineteenOffSelector ),
    ( 'ss20',   kStylisticAlternativesType, kStylisticAltTwentyOnSelector,          kStylisticAltTwentyOffSelector ),
    ( 'subs',   kVerticalPositionType,      kInferiorsSelector,                     kNormalPositionSelector ),
    ( 'sups',   kVerticalPositionType,      kSuperiorsSelector,                     kNormalPositionSelector ),
    ( 'swsh',   kContextualAlternatesType,  kSwashAlternatesOnSelector,             kSwashAlternatesOffSelector ),
    ( 'titl',   kStyleOptionsType,          kTitlingCapsSelector,                   kNoStyleOptionsSelector ),
    ( 'tnam',   kCharacterShapeType,        kTraditionalNamesCharactersSelector,    16 ),
    ( 'tnum',   kNumberSpacingType,         kMonospacedNumbersSelector,             4 ),
    ( 'trad',   kCharacterShapeType,        kTraditionalCharactersSelector,         16 ),
    ( 'twid',   kTextSpacingType,           kThirdWidthTextSelector,                7 ),
    ( 'unic',   kLetterCaseType,            14,                                     15 ),
    ( 'valt',   kTextSpacingType,           kAltProportionalTextSelector,           7 ),
    ( 'vert',   kVerticalSubstitutionType,  kSubstituteVerticalFormsOnSelector,     kSubstituteVerticalFormsOffSelector ),
    ( 'vhal',   kTextSpacingType,           kAltHalfWidthTextSelector,              7 ),
    ( 'vkna',   kAlternateKanaType,         kAlternateVertKanaOnSelector,           kAlternateVertKanaOffSelector ),
    ( 'vpal',   kTextSpacingType,           kAltProportionalTextSelector,           7 ),
    ( 'vrt2',   kVerticalSubstitutionType,  kSubstituteVerticalFormsOnSelector,     kSubstituteVerticalFormsOffSelector ),
    ( 'zero',   kTypographicExtrasType,     kSlashedZeroOnSelector,                 kSlashedZeroOffSelector ),
    ]

_featureMap = dict()
for tag, sel, on, off in _coreTextfeatureData:
    _featureMap[tag] = sel, on
    _featureMap["%s_off" % tag] = sel, off

featureMap = dict()
reversedFeatureMap = dict()

for key, value in _featureMap.items():
    featureType, featureSelector = value
    feature = {
        CoreText.NSFontFeatureTypeIdentifierKey: featureType,
        CoreText.NSFontFeatureSelectorIdentifierKey: featureSelector
    }
    featureMap[key] = feature
    reversedFeatureMap[(featureType, featureSelector)] = key
