import unittest
import sys
import drawBot
from testSupport import DrawBotBaseTest

sourceImagePath = "data/drawBot144.png"
sampleImage = drawBot.ImageObject("data/drawBot.png")
sampleFormattedString = drawBot.FormattedString("Hello World")
sampleText = drawBot.FormattedString("Hello World")


class ImageObjectTest(DrawBotBaseTest):

    def test_accordionFoldTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.accordionFoldTransition(targetImage=sampleImage, bottomHeight=0.0, numberOfFolds=3.0, foldShadowAmount=0.1, time=0.0)
        img._applyFilters()

    def test_additionCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.additionCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_affineClamp(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.affineClamp(transform=(0.4, 0.0, 0.0, 0.4, 0.0, 0.0))
        img._applyFilters()

    def test_affineTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.affineTile(transform=(0.4, 0.0, 0.0, 0.4, 0.0, 0.0))
        img._applyFilters()

    def test_areaAlphaWeightedHistogram(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaAlphaWeightedHistogram(extent=(0.0, 0.0, 640.0, 80.0), scale=1.0, count=64.0)
        img._applyFilters()

    def test_areaAverage(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaAverage(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_areaBoundsRed(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaBoundsRed(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_areaHistogram(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaHistogram(extent=(0.0, 0.0, 640.0, 80.0), scale=1.0, count=64.0)
        img._applyFilters()

    def test_areaLogarithmicHistogram(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaLogarithmicHistogram(extent=(0.0, 0.0, 640.0, 80.0), scale=1.0, count=64.0, minimumStop=-10.0, maximumStop=4.0)
        img._applyFilters()

    def test_areaMaximum(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaMaximum(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_areaMaximumAlpha(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaMaximumAlpha(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_areaMinimum(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaMinimum(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_areaMinimumAlpha(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaMinimumAlpha(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_areaMinMax(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaMinMax(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_areaMinMaxRed(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.areaMinMaxRed(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_aztecCodeGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.aztecCodeGenerator(size=(100, 100), message=b'Hello World', layers=None, compactStyle=None, correctionLevel=23.0)
        img._applyFilters()

    def test_barsSwipeTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.barsSwipeTransition(targetImage=sampleImage, angle=3.141592653589793, width=30.0, barOffset=10.0, time=0.0)
        img._applyFilters()

    def test_blendWithAlphaMask(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.blendWithAlphaMask(backgroundImage=sampleImage, maskImage=sampleImage)
        img._applyFilters()

    def test_blendWithBlueMask(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.blendWithBlueMask(backgroundImage=sampleImage, maskImage=sampleImage)
        img._applyFilters()

    def test_blendWithMask(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.blendWithMask(backgroundImage=sampleImage, maskImage=sampleImage)
        img._applyFilters()

    def test_blendWithRedMask(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.blendWithRedMask(backgroundImage=sampleImage, maskImage=sampleImage)
        img._applyFilters()

    def test_bloom(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.bloom(radius=10.0, intensity=0.5)
        img._applyFilters()

    def test_blurredRectangleGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.blurredRectangleGenerator(size=(100, 100), extent=(0.0, 0.0, 100.0, 100.0), sigma=10.0, color=(1.0, 1.0, 1.0, 1.0))
        img._applyFilters()

    def test_bokehBlur(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.bokehBlur(radius=20.0, ringAmount=0.0, ringSize=0.1, softness=1.0)
        img._applyFilters()

    def test_boxBlur(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.boxBlur(radius=10.0)
        img._applyFilters()

    def test_bumpDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.bumpDistortion(center=(150.0, 150.0), radius=300.0, scale=0.5)
        img._applyFilters()

    def test_bumpDistortionLinear(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.bumpDistortionLinear(center=(150.0, 150.0), radius=300.0, angle=0.0, scale=0.5)
        img._applyFilters()

    def test_cannyEdgeDetector(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.cannyEdgeDetector(gaussianSigma=1.6, perceptual=False, thresholdHigh=0.05, thresholdLow=0.02, hysteresisPasses=1.0)
        img._applyFilters()

    def test_checkerboardGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.checkerboardGenerator(size=(100, 100), center=(150.0, 150.0), color0=(1.0, 1.0, 1.0, 1.0), color1=(0.0, 0.0, 0.0, 1.0), width=80.0, sharpness=1.0)
        img._applyFilters()

    def test_circleSplashDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.circleSplashDistortion(center=(150.0, 150.0), radius=150.0)
        img._applyFilters()

    def test_circularScreen(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.circularScreen(center=(150.0, 150.0), width=6.0, sharpness=0.7)
        img._applyFilters()

    def test_circularWrap(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.circularWrap(center=(150.0, 150.0), radius=150.0, angle=0.0)
        img._applyFilters()

    def test_clamp(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.clamp(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_CMYKHalftone(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.CMYKHalftone(center=(150.0, 150.0), width=6.0, angle=0.0, sharpness=0.7, GCR=1.0, UCR=0.5)
        img._applyFilters()

    def test_code128BarcodeGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.code128BarcodeGenerator(size=(100, 100), message=b'Hello World', quietSpace=10.0, barcodeHeight=32.0)
        img._applyFilters()

    def test_colorAbsoluteDifference(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorAbsoluteDifference(image2=None)
        img._applyFilters()

    def test_colorBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_colorBurnBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorBurnBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_colorClamp(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorClamp(minComponents=(0.0, 0.0, 0.0, 0.0), maxComponents=(1.0, 1.0, 1.0, 1.0))
        img._applyFilters()

    def test_colorControls(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorControls(saturation=1.0, brightness=0.0, contrast=1.0)
        img._applyFilters()

    def test_colorCrossPolynomial(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorCrossPolynomial(redCoefficients=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), greenCoefficients=(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), blueCoefficients=(0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        img._applyFilters()

    def test_colorDodgeBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorDodgeBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_colorInvert(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorInvert()
        img._applyFilters()

    def test_colorMap(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorMap(gradientImage=sampleImage)
        img._applyFilters()

    def test_colorMatrix(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorMatrix(RVector=(1.0, 0.0, 0.0, 0.0), GVector=(0.0, 1.0, 0.0, 0.0), BVector=(0.0, 0.0, 1.0, 0.0), AVector=(0.0, 0.0, 0.0, 1.0), biasVector=(0.0, 0.0, 0.0, 0.0))
        img._applyFilters()

    def test_colorMonochrome(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorMonochrome(color=(0.6, 0.45, 0.3, 1.0), intensity=1.0)
        img._applyFilters()

    def test_colorPolynomial(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorPolynomial(redCoefficients=(0.0, 1.0, 0.0, 0.0), greenCoefficients=(0.0, 1.0, 0.0, 0.0), blueCoefficients=(0.0, 1.0, 0.0, 0.0), alphaCoefficients=(0.0, 1.0, 0.0, 0.0))
        img._applyFilters()

    def test_colorPosterize(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorPosterize(levels=6.0)
        img._applyFilters()

    def test_colorThreshold(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorThreshold(threshold=0.5)
        img._applyFilters()

    def test_colorThresholdOtsu(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.colorThresholdOtsu()
        img._applyFilters()

    def test_columnAverage(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.columnAverage(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_comicEffect(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.comicEffect()
        img._applyFilters()

    def test_constantColorGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.constantColorGenerator(size=(100, 100), color=(1.0, 0.0, 0.0, 1.0))
        img._applyFilters()

    def test_convertLabToRGB(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.convertLabToRGB(normalize=False)
        img._applyFilters()

    def test_convertRGBtoLab(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.convertRGBtoLab(normalize=False)
        img._applyFilters()

    def test_copyMachineTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.copyMachineTransition(targetImage=sampleImage, extent=(0.0, 0.0, 300.0, 300.0), color=(0.6, 1.0, 0.8, 1.0), time=0.0, angle=0.0, width=200.0, opacity=1.3)
        img._applyFilters()

    def test_crop(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.crop(rectangle=(-8.988465674311579e+307, -8.988465674311579e+307, 1.7976931348623157e+308, 1.7976931348623157e+308))
        img._applyFilters()

    def test_crystallize(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.crystallize(radius=20.0, center=(150.0, 150.0))
        img._applyFilters()

    def test_darkenBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.darkenBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_depthOfField(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.depthOfField(point0=(0.0, 300.0), point1=(300.0, 300.0), saturation=1.5, unsharpMaskRadius=2.5, unsharpMaskIntensity=0.5, radius=6.0)
        img._applyFilters()

    def test_depthToDisparity(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.depthToDisparity()
        img._applyFilters()

    def test_differenceBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.differenceBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_discBlur(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.discBlur(radius=8.0)
        img._applyFilters()

    def test_disintegrateWithMaskTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.disintegrateWithMaskTransition(targetImage=sampleImage, maskImage=sampleImage, time=0.0, shadowRadius=8.0, shadowDensity=0.65, shadowOffset=(0.0, -10.0))
        img._applyFilters()

    def test_disparityToDepth(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.disparityToDepth()
        img._applyFilters()

    def test_displacementDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.displacementDistortion(displacementImage=sampleImage, scale=50.0)
        img._applyFilters()

    def test_dissolveTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.dissolveTransition(targetImage=sampleImage, time=0.0)
        img._applyFilters()

    def test_distanceGradientFromRedMask(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.distanceGradientFromRedMask(maximumDistance=10.0)
        img._applyFilters()

    def test_dither(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.dither(intensity=0.1)
        img._applyFilters()

    def test_divideBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.divideBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_documentEnhancer(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.documentEnhancer(amount=1.0)
        img._applyFilters()

    def test_dotScreen(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.dotScreen(center=(150.0, 150.0), angle=0.0, width=6.0, sharpness=0.7)
        img._applyFilters()

    def test_droste(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.droste(insetPoint0=(200.0, 200.0), insetPoint1=(400.0, 400.0), strands=1.0, periodicity=1.0, rotation=0.0, zoom=1.0)
        img._applyFilters()

    def test_edgePreserveUpsampleFilter(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.edgePreserveUpsampleFilter(smallImage=sampleImage, spatialSigma=3.0, lumaSigma=0.15)
        img._applyFilters()

    def test_edges(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.edges(intensity=1.0)
        img._applyFilters()

    def test_edgeWork(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.edgeWork(radius=3.0)
        img._applyFilters()

    def test_eightfoldReflectedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.eightfoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)
        img._applyFilters()

    def test_exclusionBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.exclusionBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_exposureAdjust(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.exposureAdjust(EV=0.0)
        img._applyFilters()

    def test_falseColor(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.falseColor(color0=(0.3, 0.0, 0.0, 1.0), color1=(1.0, 0.9, 0.8, 1.0))
        img._applyFilters()

    def test_flashTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.flashTransition(targetImage=sampleImage, center=(150.0, 150.0), extent=(0.0, 0.0, 300.0, 300.0), color=(1.0, 0.8, 0.6, 1.0), time=0.0, maxStriationRadius=2.58, striationStrength=0.5, striationContrast=1.375, fadeThreshold=0.85)
        img._applyFilters()

    def test_fourfoldReflectedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.fourfoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0, acuteAngle=1.5707963267948966)
        img._applyFilters()

    def test_fourfoldRotatedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.fourfoldRotatedTile(center=(150.0, 150.0), angle=0.0, width=100.0)
        img._applyFilters()

    def test_fourfoldTranslatedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.fourfoldTranslatedTile(center=(150.0, 150.0), angle=0.0, width=100.0, acuteAngle=1.5707963267948966)
        img._applyFilters()

    def test_gaborGradients(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.gaborGradients()
        img._applyFilters()

    def test_gammaAdjust(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.gammaAdjust(power=1.0)
        img._applyFilters()

    def test_gaussianBlur(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.gaussianBlur(radius=10.0)
        img._applyFilters()

    def test_gaussianGradient(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.gaussianGradient(size=(100, 100), center=(150.0, 150.0), color0=(1.0, 1.0, 1.0, 1.0), color1=(0.0, 0.0, 0.0, 0.0), radius=300.0)
        img._applyFilters()

    def test_glassDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.glassDistortion(texture=sampleImage, center=(150.0, 150.0), scale=200.0)
        img._applyFilters()

    def test_glassLozenge(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.glassLozenge(point0=(150.0, 150.0), point1=(350.0, 150.0), radius=100.0, refraction=1.7)
        img._applyFilters()

    def test_glideReflectedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.glideReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)
        img._applyFilters()

    def test_gloom(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.gloom(radius=10.0, intensity=0.5)
        img._applyFilters()

    def test_guidedFilter(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.guidedFilter(guideImage=sampleImage, radius=1.0, epsilon=0.0001)
        img._applyFilters()

    def test_hardLightBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.hardLightBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_hatchedScreen(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.hatchedScreen(center=(150.0, 150.0), angle=0.0, width=6.0, sharpness=0.7)
        img._applyFilters()

    def test_heightFieldFromMask(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.heightFieldFromMask(radius=10.0)
        img._applyFilters()

    def test_hexagonalPixellate(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.hexagonalPixellate(center=(150.0, 150.0), scale=8.0)
        img._applyFilters()

    def test_highlightShadowAdjust(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.highlightShadowAdjust(radius=0.0, shadowAmount=0.0, highlightAmount=1.0)
        img._applyFilters()

    def test_histogramDisplayFilter(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.histogramDisplayFilter(height=100.0, highLimit=1.0, lowLimit=0.0)
        img._applyFilters()

    def test_holeDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.holeDistortion(center=(150.0, 150.0), radius=150.0)
        img._applyFilters()

    def test_hueAdjust(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.hueAdjust(angle=0.0)
        img._applyFilters()

    def test_hueBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.hueBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_kaleidoscope(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.kaleidoscope(count=6.0, center=(150.0, 150.0), angle=0.0)
        img._applyFilters()

    def test_keystoneCorrectionCombined(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.keystoneCorrectionCombined(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), focalLength=28.0)
        img._applyFilters()

    def test_keystoneCorrectionHorizontal(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.keystoneCorrectionHorizontal(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), focalLength=28.0)
        img._applyFilters()

    def test_keystoneCorrectionVertical(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.keystoneCorrectionVertical(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), focalLength=28.0)
        img._applyFilters()

    def test_KMeans(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.KMeans(means=None, extent=(0.0, 0.0, 640.0, 80.0), count=8.0, passes=5.0, perceptual=False)
        img._applyFilters()

    def test_labDeltaE(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.labDeltaE(image2=None)
        img._applyFilters()

    def test_lanczosScaleTransform(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.lanczosScaleTransform(scale=1.0, aspectRatio=1.0)
        img._applyFilters()

    def test_lenticularHaloGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.lenticularHaloGenerator(size=(100, 100), center=(150.0, 150.0), color=(1.0, 0.9, 0.8, 1.0), haloRadius=70.0, haloWidth=87.0, haloOverlap=0.77, striationStrength=0.5, striationContrast=1.0, time=0.0)
        img._applyFilters()

    def test_lightenBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.lightenBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_lightTunnel(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.lightTunnel(center=(150.0, 150.0), rotation=0.0, radius=100.0)
        img._applyFilters()

    def test_linearBurnBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.linearBurnBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_linearDodgeBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.linearDodgeBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_linearGradient(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.linearGradient(size=(100, 100), point0=(0.0, 0.0), point1=(200.0, 200.0), color0=(1.0, 1.0, 1.0, 1.0), color1=(0.0, 0.0, 0.0, 1.0))
        img._applyFilters()

    def test_linearLightBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.linearLightBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_linearToSRGBToneCurve(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.linearToSRGBToneCurve()
        img._applyFilters()

    def test_lineOverlay(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.lineOverlay(NRNoiseLevel=0.07, NRSharpness=0.71, edgeIntensity=1.0, threshold=0.1, contrast=50.0)
        img._applyFilters()

    def test_lineScreen(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.lineScreen(center=(150.0, 150.0), angle=0.0, width=6.0, sharpness=0.7)
        img._applyFilters()

    def test_luminosityBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.luminosityBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_maskedVariableBlur(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.maskedVariableBlur(mask=sampleImage, radius=5.0)
        img._applyFilters()

    def test_maskToAlpha(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.maskToAlpha()
        img._applyFilters()

    def test_maximumComponent(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.maximumComponent()
        img._applyFilters()

    def test_maximumCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.maximumCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_maximumScaleTransform(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.maximumScaleTransform(scale=1.0, aspectRatio=1.0)
        img._applyFilters()

    def test_meshGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.meshGenerator(size=(100, 100), mesh=None, width=1.5, color=(1.0, 1.0, 1.0, 1.0))
        img._applyFilters()

    def test_minimumComponent(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.minimumComponent()
        img._applyFilters()

    def test_minimumCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.minimumCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_mix(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.mix(backgroundImage=sampleImage, amount=1.0)
        img._applyFilters()

    def test_modTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.modTransition(targetImage=sampleImage, center=(150.0, 150.0), time=0.0, angle=2.0, radius=150.0, compression=300.0)
        img._applyFilters()

    def test_morphologyGradient(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.morphologyGradient(radius=5.0)
        img._applyFilters()

    def test_morphologyMaximum(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.morphologyMaximum(radius=0.0)
        img._applyFilters()

    def test_morphologyMinimum(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.morphologyMinimum(radius=0.0)
        img._applyFilters()

    def test_morphologyRectangleMaximum(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.morphologyRectangleMaximum(width=5.0, height=5.0)
        img._applyFilters()

    def test_morphologyRectangleMinimum(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.morphologyRectangleMinimum(width=5.0, height=5.0)
        img._applyFilters()

    def test_motionBlur(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.motionBlur(radius=20.0, angle=0.0)
        img._applyFilters()

    def test_multiplyBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.multiplyBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_multiplyCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.multiplyCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_ninePartStretched(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.ninePartStretched(breakpoint0=(50.0, 50.0), breakpoint1=(150.0, 150.0), growAmount=(100.0, 100.0))
        img._applyFilters()

    def test_ninePartTiled(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.ninePartTiled(breakpoint0=(50.0, 50.0), breakpoint1=(150.0, 150.0), growAmount=(100.0, 100.0), flipYTiles=True)
        img._applyFilters()

    def test_noiseReduction(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.noiseReduction(noiseLevel=0.02, sharpness=0.4)
        img._applyFilters()

    def test_opTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.opTile(center=(150.0, 150.0), scale=2.8, angle=0.0, width=65.0)
        img._applyFilters()

    def test_overlayBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.overlayBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_pageCurlTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.pageCurlTransition(targetImage=sampleImage, backsideImage=sampleImage, shadingImage=sampleImage, extent=(0.0, 0.0, 300.0, 300.0), time=0.0, angle=0.0, radius=100.0)
        img._applyFilters()

    def test_pageCurlWithShadowTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.pageCurlWithShadowTransition(targetImage=sampleImage, backsideImage=sampleImage, extent=(0.0, 0.0, 0.0, 0.0), time=0.0, angle=0.0, radius=100.0, shadowSize=0.5, shadowAmount=0.7, shadowExtent=(0.0, 0.0, 0.0, 0.0))
        img._applyFilters()

    def test_paletteCentroid(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.paletteCentroid(paletteImage=sampleImage, perceptual=False)
        img._applyFilters()

    def test_palettize(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.palettize(paletteImage=sampleImage, perceptual=False)
        img._applyFilters()

    def test_parallelogramTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.parallelogramTile(center=(150.0, 150.0), angle=0.0, acuteAngle=1.5707963267948966, width=100.0)
        img._applyFilters()

    def test_PDF417BarcodeGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.PDF417BarcodeGenerator(size=(100, 100), message=b'Hello World', minWidth=None, maxWidth=None, minHeight=None, maxHeight=None, dataColumns=None, rows=None, preferredAspectRatio=None, compactionMode=None, compactStyle=None, correctionLevel=None, alwaysSpecifyCompaction=None)
        img._applyFilters()

    def test_personSegmentation(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.personSegmentation(qualityLevel=0.0)
        img._applyFilters()

    def test_perspectiveCorrection(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.perspectiveCorrection(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), crop=True)
        img._applyFilters()

    def test_perspectiveRotate(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.perspectiveRotate(focalLength=28.0, pitch=0.0, yaw=0.0, roll=0.0)
        img._applyFilters()

    def test_perspectiveTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.perspectiveTile(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2))
        img._applyFilters()

    def test_perspectiveTransform(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.perspectiveTransform(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2))
        img._applyFilters()

    def test_perspectiveTransformWithExtent(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.perspectiveTransformWithExtent(extent=(0.0, 0.0, 300.0, 300.0), topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2))
        img._applyFilters()

    def test_photoEffectChrome(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectChrome(extrapolate=False)
        img._applyFilters()

    def test_photoEffectFade(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectFade(extrapolate=False)
        img._applyFilters()

    def test_photoEffectInstant(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectInstant(extrapolate=False)
        img._applyFilters()

    def test_photoEffectMono(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectMono(extrapolate=False)
        img._applyFilters()

    def test_photoEffectNoir(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectNoir(extrapolate=False)
        img._applyFilters()

    def test_photoEffectProcess(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectProcess(extrapolate=False)
        img._applyFilters()

    def test_photoEffectTonal(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectTonal(extrapolate=False)
        img._applyFilters()

    def test_photoEffectTransfer(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.photoEffectTransfer(extrapolate=False)
        img._applyFilters()

    def test_pinchDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.pinchDistortion(center=(150.0, 150.0), radius=300.0, scale=0.5)
        img._applyFilters()

    def test_pinLightBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.pinLightBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_pixellate(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.pixellate(center=(150.0, 150.0), scale=8.0)
        img._applyFilters()

    def test_pointillize(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.pointillize(radius=20.0, center=(150.0, 150.0))
        img._applyFilters()

    def test_QRCodeGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.QRCodeGenerator(size=(100, 100), message=b'Hello World', correctionLevel='M')
        img._applyFilters()

    def test_radialGradient(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.radialGradient(size=(100, 100), center=(150.0, 150.0), radius0=5.0, radius1=100.0, color0=(1.0, 1.0, 1.0, 1.0), color1=(0.0, 0.0, 0.0, 1.0))
        img._applyFilters()

    def test_randomGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.randomGenerator(size=(100, 100))
        img._applyFilters()

    def test_rippleTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.rippleTransition(targetImage=sampleImage, shadingImage=sampleImage, center=(150.0, 150.0), extent=(0.0, 0.0, 300.0, 300.0), time=0.0, width=100.0, scale=50.0)
        img._applyFilters()

    def test_roundedRectangleGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.roundedRectangleGenerator(size=(100, 100), extent=(0.0, 0.0, 100.0, 100.0), radius=10.0, color=(1.0, 1.0, 1.0, 1.0))
        img._applyFilters()

    def test_roundedRectangleStrokeGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.roundedRectangleStrokeGenerator(size=(100, 100), extent=(0.0, 0.0, 100.0, 100.0), radius=10.0, color=(1.0, 1.0, 1.0, 1.0), width=10.0)
        img._applyFilters()

    def test_rowAverage(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.rowAverage(extent=(0.0, 0.0, 640.0, 80.0))
        img._applyFilters()

    def test_saliencyMapFilter(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.saliencyMapFilter()
        img._applyFilters()

    def test_sampleNearest(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sampleNearest()
        img._applyFilters()

    def test_saturationBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.saturationBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_screenBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.screenBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_sepiaTone(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sepiaTone(intensity=1.0)
        img._applyFilters()

    def test_shadedMaterial(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.shadedMaterial(shadingImage=sampleImage, scale=10.0)
        img._applyFilters()

    def test_sharpenLuminance(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sharpenLuminance(sharpness=0.4, radius=1.69)
        img._applyFilters()

    def test_sixfoldReflectedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sixfoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)
        img._applyFilters()

    def test_sixfoldRotatedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sixfoldRotatedTile(center=(150.0, 150.0), angle=0.0, width=100.0)
        img._applyFilters()

    def test_smoothLinearGradient(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.smoothLinearGradient(size=(100, 100), point0=(0.0, 0.0), point1=(200.0, 200.0), color0=(1.0, 1.0, 1.0, 1.0), color1=(0.0, 0.0, 0.0, 1.0))
        img._applyFilters()

    def test_sobelGradients(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sobelGradients()
        img._applyFilters()

    def test_softLightBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.softLightBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_sourceAtopCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sourceAtopCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_sourceInCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sourceInCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_sourceOutCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sourceOutCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_sourceOverCompositing(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sourceOverCompositing(backgroundImage=sampleImage)
        img._applyFilters()

    def test_spotColor(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.spotColor(centerColor1=(0.0784, 0.0627, 0.0706, 1.0), replacementColor1=(0.4392, 0.1922, 0.1961, 1.0), closeness1=0.22, contrast1=0.98, centerColor2=(0.5255, 0.3059, 0.3451, 1.0), replacementColor2=(0.9137, 0.5608, 0.5059, 1.0), closeness2=0.15, contrast2=0.98, centerColor3=(0.9216, 0.4549, 0.3333, 1.0), replacementColor3=(0.9098, 0.7529, 0.6078, 1.0), closeness3=0.5, contrast3=0.99)
        img._applyFilters()

    def test_spotLight(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.spotLight(lightPosition=(400.0, 600.0, 150.0), lightPointsAt=(200.0, 200.0, 0.0), brightness=3.0, concentration=0.1, color=(1.0, 1.0, 1.0, 1.0))
        img._applyFilters()

    def test_SRGBToneCurveToLinear(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.SRGBToneCurveToLinear()
        img._applyFilters()

    def test_starShineGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.starShineGenerator(size=(100, 100), center=(150.0, 150.0), color=(1.0, 0.8, 0.6, 1.0), radius=50.0, crossScale=15.0, crossAngle=0.6, crossOpacity=-2.0, crossWidth=2.5, epsilon=-2.0)
        img._applyFilters()

    def test_straightenFilter(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.straightenFilter(angle=0.0)
        img._applyFilters()

    def test_stretchCrop(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.stretchCrop(size=(1280.0, 720.0), cropAmount=0.25, centerStretchAmount=0.25)
        img._applyFilters()

    def test_stripesGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.stripesGenerator(size=(100, 100), center=(150.0, 150.0), color0=(1.0, 1.0, 1.0, 1.0), color1=(0.0, 0.0, 0.0, 1.0), width=80.0, sharpness=1.0)
        img._applyFilters()

    def test_subtractBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.subtractBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_sunbeamsGenerator(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.sunbeamsGenerator(size=(100, 100), center=(150.0, 150.0), color=(1.0, 0.5, 0.0, 1.0), sunRadius=40.0, maxStriationRadius=2.58, striationStrength=0.5, striationContrast=1.375, time=0.0)
        img._applyFilters()

    def test_swipeTransition(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.swipeTransition(targetImage=sampleImage, extent=(0.0, 0.0, 300.0, 300.0), color=(1.0, 1.0, 1.0, 1.0), time=0.0, angle=0.0, width=300.0, opacity=0.0)
        img._applyFilters()

    def test_temperatureAndTint(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.temperatureAndTint(neutral=(6500.0, 0.0), targetNeutral=(6500.0, 0.0))
        img._applyFilters()

    def test_thermal(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.thermal()
        img._applyFilters()

    def test_toneCurve(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.toneCurve(point0=(0.0, 0.0), point1=(0.25, 0.25), point2=(0.5, 0.5), point3=(0.75, 0.75), point4=(1.0, 1.0), extrapolate=False)
        img._applyFilters()

    def test_toneMapHeadroom(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.toneMapHeadroom(sourceHeadroom=None, targetHeadroom=1.0)
        img._applyFilters()

    def test_torusLensDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.torusLensDistortion(center=(150.0, 150.0), radius=160.0, width=80.0, refraction=1.7)
        img._applyFilters()

    def test_triangleKaleidoscope(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.triangleKaleidoscope(point=(150.0, 150.0), size=700.0, rotation=5.924285296593801, decay=0.85)
        img._applyFilters()

    def test_triangleTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.triangleTile(center=(150.0, 150.0), angle=0.0, width=100.0)
        img._applyFilters()

    def test_twelvefoldReflectedTile(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.twelvefoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)
        img._applyFilters()

    def test_twirlDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.twirlDistortion(center=(150.0, 150.0), radius=300.0, angle=3.141592653589793)
        img._applyFilters()

    def test_unsharpMask(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.unsharpMask(radius=2.5, intensity=0.5)
        img._applyFilters()

    def test_vibrance(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.vibrance(amount=0.0)
        img._applyFilters()

    def test_vignette(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.vignette(intensity=0.0, radius=1.0)
        img._applyFilters()

    def test_vignetteEffect(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.vignetteEffect(center=(150.0, 150.0), radius=150.0, intensity=1.0, falloff=0.5)
        img._applyFilters()

    def test_vividLightBlendMode(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.vividLightBlendMode(backgroundImage=sampleImage)
        img._applyFilters()

    def test_vortexDistortion(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.vortexDistortion(center=(150.0, 150.0), radius=300.0, angle=56.548667764616276)
        img._applyFilters()

    def test_whitePointAdjust(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.whitePointAdjust(color=(1.0, 1.0, 1.0, 1.0))
        img._applyFilters()

    def test_XRay(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.XRay()
        img._applyFilters()

    def test_zoomBlur(self):
        img = drawBot.ImageObject(sourceImagePath)
        img.zoomBlur(center=(150.0, 150.0), amount=20.0)
        img._applyFilters()

if __name__ == '__main__':
    sys.exit(unittest.main())
