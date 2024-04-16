import unittest
import sys
import drawBot
from testSupport import DrawBotBaseTest

class ImageObjectTest(DrawBotBaseTest):

    def test_accordionFoldTransition(self):
        pass

    def test_additionCompositing(self):
        pass

    def test_affineClamp(self):
        pass

    def test_affineTile(self):
        pass

    def test_areaAverage(self):
        pass

    def test_areaHistogram(self):
        pass

    def test_areaLogarithmicHistogram(self):
        pass

    def test_areaMaximum(self):
        pass

    def test_areaMaximumAlpha(self):
        pass

    def test_areaMinimum(self):
        pass

    def test_areaMinimumAlpha(self):
        pass

    def test_areaMinMax(self):
        pass

    def test_areaMinMaxRed(self):
        pass

    def test_attributedTextImageGenerator(self):
        img = drawBot.ImageObject()
        img.attributedTextImageGenerator((100, 100), b'hello world')

    def test_aztecCodeGenerator(self):
        img = drawBot.ImageObject()
        img.aztecCodeGenerator((100, 100), b'hello world')

    def test_barsSwipeTransition(self):
        pass

    def test_blendWithAlphaMask(self):
        pass

    def test_blendWithBlueMask(self):
        pass

    def test_blendWithMask(self):
        pass

    def test_blendWithRedMask(self):
        pass

    def test_bloom(self):
        pass

    def test_blurredRectangleGenerator(self):
        img = drawBot.ImageObject()
        img.blurredRectangleGenerator((100, 100), b'hello world')

    def test_bokehBlur(self):
        pass

    def test_boxBlur(self):
        pass

    def test_bumpDistortion(self):
        pass

    def test_bumpDistortionLinear(self):
        pass

    def test_cannyEdgeDetector(self):
        pass

    def test_checkerboardGenerator(self):
        img = drawBot.ImageObject()
        img.checkerboardGenerator((100, 100), b'hello world')

    def test_circleSplashDistortion(self):
        pass

    def test_circularScreen(self):
        pass

    def test_circularWrap(self):
        pass

    def test_clamp(self):
        pass

    def test_CMYKHalftone(self):
        pass

    def test_code128BarcodeGenerator(self):
        img = drawBot.ImageObject()
        img.code128BarcodeGenerator((100, 100), b'hello world')

    def test_colorAbsoluteDifference(self):
        pass

    def test_colorBlendMode(self):
        pass

    def test_colorBurnBlendMode(self):
        pass

    def test_colorClamp(self):
        pass

    def test_colorControls(self):
        pass

    def test_colorCrossPolynomial(self):
        pass

    def test_colorCurves(self):
        pass

    def test_colorDodgeBlendMode(self):
        pass

    def test_colorInvert(self):
        pass

    def test_colorMap(self):
        pass

    def test_colorMatrix(self):
        pass

    def test_colorMonochrome(self):
        pass

    def test_colorPolynomial(self):
        pass

    def test_colorPosterize(self):
        pass

    def test_colorThreshold(self):
        pass

    def test_colorThresholdOtsu(self):
        pass

    def test_columnAverage(self):
        pass

    def test_comicEffect(self):
        pass

    def test_constantColorGenerator(self):
        img = drawBot.ImageObject()
        img.constantColorGenerator((100, 100), b'hello world')

    def test_convertLabToRGB(self):
        pass

    def test_convertRGBtoLab(self):
        pass

    def test_convolution3X3(self):
        pass

    def test_convolution5X5(self):
        pass

    def test_convolution7X7(self):
        pass

    def test_convolution9Horizontal(self):
        pass

    def test_convolution9Vertical(self):
        pass

    def test_convolutionRGB3X3(self):
        pass

    def test_convolutionRGB5X5(self):
        pass

    def test_convolutionRGB7X7(self):
        pass

    def test_convolutionRGB9Horizontal(self):
        pass

    def test_convolutionRGB9Vertical(self):
        pass

    def test_copyMachineTransition(self):
        pass

    def test_coreMLModelFilter(self):
        pass

    def test_crop(self):
        pass

    def test_crystallize(self):
        pass

    def test_darkenBlendMode(self):
        pass

    def test_depthBlurEffect(self):
        pass

    def test_depthOfField(self):
        pass

    def test_depthToDisparity(self):
        pass

    def test_differenceBlendMode(self):
        pass

    def test_discBlur(self):
        pass

    def test_disintegrateWithMaskTransition(self):
        pass

    def test_disparityToDepth(self):
        pass

    def test_displacementDistortion(self):
        pass

    def test_dissolveTransition(self):
        pass

    def test_dither(self):
        pass

    def test_divideBlendMode(self):
        pass

    def test_documentEnhancer(self):
        pass

    def test_dotScreen(self):
        pass

    def test_droste(self):
        pass

    def test_edgePreserveUpsampleFilter(self):
        pass

    def test_edges(self):
        pass

    def test_edgeWork(self):
        pass

    def test_eightfoldReflectedTile(self):
        pass

    def test_exclusionBlendMode(self):
        pass

    def test_exposureAdjust(self):
        pass

    def test_falseColor(self):
        pass

    def test_flashTransition(self):
        pass

    def test_fourfoldReflectedTile(self):
        pass

    def test_fourfoldRotatedTile(self):
        pass

    def test_fourfoldTranslatedTile(self):
        pass

    def test_gaborGradients(self):
        pass

    def test_gammaAdjust(self):
        pass

    def test_gaussianBlur(self):
        pass

    def test_gaussianGradient(self):
        img = drawBot.ImageObject()
        img.gaussianGradient((100, 100), b'hello world')

    def test_glassDistortion(self):
        pass

    def test_glassLozenge(self):
        pass

    def test_glideReflectedTile(self):
        pass

    def test_gloom(self):
        pass

    def test_guidedFilter(self):
        pass

    def test_hardLightBlendMode(self):
        pass

    def test_hatchedScreen(self):
        pass

    def test_heightFieldFromMask(self):
        pass

    def test_hexagonalPixellate(self):
        pass

    def test_highlightShadowAdjust(self):
        pass

    def test_histogramDisplayFilter(self):
        pass

    def test_holeDistortion(self):
        pass

    def test_hueAdjust(self):
        pass

    def test_hueBlendMode(self):
        pass

    def test_hueSaturationValueGradient(self):
        pass

    def test_kaleidoscope(self):
        pass

    def test_keystoneCorrectionCombined(self):
        pass

    def test_keystoneCorrectionHorizontal(self):
        pass

    def test_keystoneCorrectionVertical(self):
        pass

    def test_KMeans(self):
        pass

    def test_labDeltaE(self):
        pass

    def test_lanczosScaleTransform(self):
        pass

    def test_lenticularHaloGenerator(self):
        img = drawBot.ImageObject()
        img.lenticularHaloGenerator((100, 100), b'hello world')

    def test_lightenBlendMode(self):
        pass

    def test_lightTunnel(self):
        pass

    def test_linearBurnBlendMode(self):
        pass

    def test_linearDodgeBlendMode(self):
        pass

    def test_linearGradient(self):
        img = drawBot.ImageObject()
        img.linearGradient((100, 100), b'hello world')

    def test_linearLightBlendMode(self):
        pass

    def test_linearToSRGBToneCurve(self):
        pass

    def test_lineOverlay(self):
        pass

    def test_lineScreen(self):
        pass

    def test_luminosityBlendMode(self):
        pass

    def test_maskedVariableBlur(self):
        pass

    def test_maskToAlpha(self):
        pass

    def test_maximumComponent(self):
        pass

    def test_maximumCompositing(self):
        pass

    def test_meshGenerator(self):
        img = drawBot.ImageObject()
        img.meshGenerator((100, 100), b'hello world')

    def test_minimumComponent(self):
        pass

    def test_minimumCompositing(self):
        pass

    def test_mix(self):
        pass

    def test_modTransition(self):
        pass

    def test_morphologyGradient(self):
        pass

    def test_morphologyMaximum(self):
        pass

    def test_morphologyMinimum(self):
        pass

    def test_morphologyRectangleMaximum(self):
        pass

    def test_morphologyRectangleMinimum(self):
        pass

    def test_motionBlur(self):
        pass

    def test_multiplyBlendMode(self):
        pass

    def test_multiplyCompositing(self):
        pass

    def test_ninePartStretched(self):
        pass

    def test_ninePartTiled(self):
        pass

    def test_noiseReduction(self):
        pass

    def test_opTile(self):
        pass

    def test_overlayBlendMode(self):
        pass

    def test_pageCurlTransition(self):
        pass

    def test_pageCurlWithShadowTransition(self):
        pass

    def test_paletteCentroid(self):
        pass

    def test_palettize(self):
        pass

    def test_parallelogramTile(self):
        pass

    def test_PDF417BarcodeGenerator(self):
        img = drawBot.ImageObject()
        img.PDF417BarcodeGenerator((100, 100), b'hello world')

    def test_personSegmentation(self):
        pass

    def test_perspectiveCorrection(self):
        pass

    def test_perspectiveRotate(self):
        pass

    def test_perspectiveTile(self):
        pass

    def test_perspectiveTransform(self):
        pass

    def test_perspectiveTransformWithExtent(self):
        pass

    def test_photoEffectChrome(self):
        pass

    def test_photoEffectFade(self):
        pass

    def test_photoEffectInstant(self):
        pass

    def test_photoEffectMono(self):
        pass

    def test_photoEffectNoir(self):
        pass

    def test_photoEffectProcess(self):
        pass

    def test_photoEffectTonal(self):
        pass

    def test_photoEffectTransfer(self):
        pass

    def test_pinchDistortion(self):
        pass

    def test_pinLightBlendMode(self):
        pass

    def test_pixellate(self):
        pass

    def test_pointillize(self):
        pass

    def test_QRCodeGenerator(self):
        img = drawBot.ImageObject()
        img.QRCodeGenerator((100, 100), b'hello world')

    def test_radialGradient(self):
        img = drawBot.ImageObject()
        img.radialGradient((100, 100), b'hello world')

    def test_randomGenerator(self):
        img = drawBot.ImageObject()
        img.randomGenerator((100, 100), b'hello world')

    def test_rippleTransition(self):
        pass

    def test_roundedRectangleGenerator(self):
        img = drawBot.ImageObject()
        img.roundedRectangleGenerator((100, 100), b'hello world')

    def test_roundedRectangleStrokeGenerator(self):
        img = drawBot.ImageObject()
        img.roundedRectangleStrokeGenerator((100, 100), b'hello world')

    def test_rowAverage(self):
        pass

    def test_saliencyMapFilter(self):
        pass

    def test_sampleNearest(self):
        pass

    def test_saturationBlendMode(self):
        pass

    def test_screenBlendMode(self):
        pass

    def test_sepiaTone(self):
        pass

    def test_shadedMaterial(self):
        pass

    def test_sharpenLuminance(self):
        pass

    def test_sixfoldReflectedTile(self):
        pass

    def test_sixfoldRotatedTile(self):
        pass

    def test_smoothLinearGradient(self):
        img = drawBot.ImageObject()
        img.smoothLinearGradient((100, 100), b'hello world')

    def test_sobelGradients(self):
        pass

    def test_softLightBlendMode(self):
        pass

    def test_sourceAtopCompositing(self):
        pass

    def test_sourceInCompositing(self):
        pass

    def test_sourceOutCompositing(self):
        pass

    def test_sourceOverCompositing(self):
        pass

    def test_spotColor(self):
        pass

    def test_spotLight(self):
        pass

    def test_SRGBToneCurveToLinear(self):
        pass

    def test_starShineGenerator(self):
        img = drawBot.ImageObject()
        img.starShineGenerator((100, 100), b'hello world')

    def test_straightenFilter(self):
        pass

    def test_stretchCrop(self):
        pass

    def test_stripesGenerator(self):
        img = drawBot.ImageObject()
        img.stripesGenerator((100, 100), b'hello world')

    def test_subtractBlendMode(self):
        pass

    def test_sunbeamsGenerator(self):
        img = drawBot.ImageObject()
        img.sunbeamsGenerator((100, 100), b'hello world')

    def test_swipeTransition(self):
        pass

    def test_temperatureAndTint(self):
        pass

    def test_textImageGenerator(self):
        img = drawBot.ImageObject()
        img.textImageGenerator((100, 100), b'hello world')

    def test_thermal(self):
        pass

    def test_toneCurve(self):
        pass

    def test_torusLensDistortion(self):
        pass

    def test_triangleKaleidoscope(self):
        pass

    def test_triangleTile(self):
        pass

    def test_twelvefoldReflectedTile(self):
        pass

    def test_twirlDistortion(self):
        pass

    def test_unsharpMask(self):
        pass

    def test_vibrance(self):
        pass

    def test_vignette(self):
        pass

    def test_vignetteEffect(self):
        pass

    def test_vividLightBlendMode(self):
        pass

    def test_vortexDistortion(self):
        pass

    def test_whitePointAdjust(self):
        pass

    def test_XRay(self):
        pass

    def test_zoomBlur(self):
        pass

if __name__ == '__main__':
    sys.exit(unittest.main())
