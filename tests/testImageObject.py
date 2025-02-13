import sys
import unittest

from testSupport import DrawBotBaseTest

import drawBot

sampleImage = drawBot.ImageObject("tests/data/drawBot.png")
fs = drawBot.FormattedString("Hello World")


class ImageObjectTest(DrawBotBaseTest):
    def test_accordionFoldTransition(self):
        img = drawBot.ImageObject()
        img.accordionFoldTransition(
            targetImage=sampleImage,
            bottomHeight=0.0,
            numberOfFolds=3.0,
            foldShadowAmount=0.1,
            time=0.0,
        )

    def test_additionCompositing(self):
        img = drawBot.ImageObject()
        img.additionCompositing(backgroundImage=sampleImage)

    def test_affineClamp(self):
        img = drawBot.ImageObject()
        img.affineClamp(transform=(0.4, 0.0, 0.0, 0.4, 0.0, 0.0))

    def test_affineTile(self):
        img = drawBot.ImageObject()
        img.affineTile(transform=(0.4, 0.0, 0.0, 0.4, 0.0, 0.0))

    def test_areaAverage(self):
        img = drawBot.ImageObject()
        img.areaAverage(extent=(0.0, 0.0, 640.0, 80.0))

    def test_areaHistogram(self):
        img = drawBot.ImageObject()
        img.areaHistogram(extent=(0.0, 0.0, 640.0, 80.0), scale=1.0, count=64.0)

    def test_areaLogarithmicHistogram(self):
        img = drawBot.ImageObject()
        img.areaLogarithmicHistogram(
            extent=(0.0, 0.0, 640.0, 80.0),
            scale=1.0,
            count=64.0,
            minimumStop=-10.0,
            maximumStop=4.0,
        )

    def test_areaMaximum(self):
        img = drawBot.ImageObject()
        img.areaMaximum(extent=(0.0, 0.0, 640.0, 80.0))

    def test_areaMaximumAlpha(self):
        img = drawBot.ImageObject()
        img.areaMaximumAlpha(extent=(0.0, 0.0, 640.0, 80.0))

    def test_areaMinimum(self):
        img = drawBot.ImageObject()
        img.areaMinimum(extent=(0.0, 0.0, 640.0, 80.0))

    def test_areaMinimumAlpha(self):
        img = drawBot.ImageObject()
        img.areaMinimumAlpha(extent=(0.0, 0.0, 640.0, 80.0))

    def test_areaMinMax(self):
        img = drawBot.ImageObject()
        img.areaMinMax(extent=(0.0, 0.0, 640.0, 80.0))

    def test_areaMinMaxRed(self):
        img = drawBot.ImageObject()
        img.areaMinMaxRed(extent=(0.0, 0.0, 640.0, 80.0))

    def test_attributedTextImageGenerator(self):
        img = drawBot.ImageObject()
        img.attributedTextImageGenerator(size=(100, 100), text=fs, scaleFactor=1.0, padding=0.0)

    def test_aztecCodeGenerator(self):
        img = drawBot.ImageObject()
        img.aztecCodeGenerator(
            size=(100, 100), message=b"Hello World", layers=None, compactStyle=None, correctionLevel=23.0
        )

    def test_barsSwipeTransition(self):
        img = drawBot.ImageObject()
        img.barsSwipeTransition(targetImage=sampleImage, angle=3.141592653589793, width=30.0, barOffset=10.0, time=0.0)

    def test_blendWithAlphaMask(self):
        img = drawBot.ImageObject()
        img.blendWithAlphaMask(backgroundImage=sampleImage, maskImage=sampleImage)

    def test_blendWithBlueMask(self):
        img = drawBot.ImageObject()
        img.blendWithBlueMask(backgroundImage=sampleImage, maskImage=sampleImage)

    def test_blendWithMask(self):
        img = drawBot.ImageObject()
        img.blendWithMask(backgroundImage=sampleImage, maskImage=sampleImage)

    def test_blendWithRedMask(self):
        img = drawBot.ImageObject()
        img.blendWithRedMask(backgroundImage=sampleImage, maskImage=sampleImage)

    def test_bloom(self):
        img = drawBot.ImageObject()
        img.bloom(radius=10.0, intensity=0.5)

    def test_blurredRectangleGenerator(self):
        img = drawBot.ImageObject()
        img.blurredRectangleGenerator(
            size=(100, 100),
            extent=(0.0, 0.0, 100.0, 100.0),
            sigma=10.0,
            color=(1.0, 1.0, 1.0, 1.0),
        )

    def test_bokehBlur(self):
        img = drawBot.ImageObject()
        img.bokehBlur(radius=20.0, ringAmount=0.0, ringSize=0.1, softness=1.0)

    def test_boxBlur(self):
        img = drawBot.ImageObject()
        img.boxBlur(radius=10.0)

    def test_bumpDistortion(self):
        img = drawBot.ImageObject()
        img.bumpDistortion(center=(150.0, 150.0), radius=300.0, scale=0.5)

    def test_bumpDistortionLinear(self):
        img = drawBot.ImageObject()
        img.bumpDistortionLinear(center=(150.0, 150.0), radius=300.0, angle=0.0, scale=0.5)

    def test_cannyEdgeDetector(self):
        img = drawBot.ImageObject()
        img.cannyEdgeDetector(
            gaussianSigma=1.6,
            perceptual=False,
            thresholdHigh=0.05,
            thresholdLow=0.02,
            hysteresisPasses=1.0,
        )

    def test_checkerboardGenerator(self):
        img = drawBot.ImageObject()
        img.checkerboardGenerator(
            size=(100, 100),
            center=(150.0, 150.0),
            color0=(1.0, 1.0, 1.0, 1.0),
            color1=(0.0, 0.0, 0.0, 1.0),
            width=80.0,
            sharpness=1.0,
        )

    def test_circleSplashDistortion(self):
        img = drawBot.ImageObject()
        img.circleSplashDistortion(center=(150.0, 150.0), radius=150.0)

    def test_circularScreen(self):
        img = drawBot.ImageObject()
        img.circularScreen(center=(150.0, 150.0), width=6.0, sharpness=0.7)

    def test_circularWrap(self):
        img = drawBot.ImageObject()
        img.circularWrap(center=(150.0, 150.0), radius=150.0, angle=0.0)

    def test_clamp(self):
        img = drawBot.ImageObject()
        img.clamp(extent=(0.0, 0.0, 640.0, 80.0))

    def test_CMYKHalftone(self):
        img = drawBot.ImageObject()
        img.CMYKHalftone(center=(150.0, 150.0), width=6.0, angle=0.0, sharpness=0.7, GCR=1.0, UCR=0.5)

    def test_code128BarcodeGenerator(self):
        img = drawBot.ImageObject()
        img.code128BarcodeGenerator(size=(100, 100), message=b"Hello World", quietSpace=10.0, barcodeHeight=32.0)

    def test_colorAbsoluteDifference(self):
        img = drawBot.ImageObject()
        img.colorAbsoluteDifference(image2=None)

    def test_colorBlendMode(self):
        img = drawBot.ImageObject()
        img.colorBlendMode(backgroundImage=sampleImage)

    def test_colorBurnBlendMode(self):
        img = drawBot.ImageObject()
        img.colorBurnBlendMode(backgroundImage=sampleImage)

    def test_colorClamp(self):
        img = drawBot.ImageObject()
        img.colorClamp(minComponents=(0.0, 0.0, 0.0, 0.0), maxComponents=(1.0, 1.0, 1.0, 1.0))

    def test_colorControls(self):
        img = drawBot.ImageObject()
        img.colorControls(saturation=1.0, brightness=0.0, contrast=1.0)

    def test_colorCrossPolynomial(self):
        img = drawBot.ImageObject()
        img.colorCrossPolynomial(
            redCoefficients=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            greenCoefficients=(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            blueCoefficients=(0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        )

    def test_colorCurves(self):
        img = drawBot.ImageObject()
        img.colorCurves(colorSpace=None, curvesData=None, curvesDomain=(0.0, 1.0))

    def test_colorDodgeBlendMode(self):
        img = drawBot.ImageObject()
        img.colorDodgeBlendMode(backgroundImage=sampleImage)

    def test_colorInvert(self):
        img = drawBot.ImageObject()
        img.colorInvert()

    def test_colorMap(self):
        img = drawBot.ImageObject()
        img.colorMap(gradientImage=sampleImage)

    def test_colorMatrix(self):
        img = drawBot.ImageObject()
        img.colorMatrix(
            RVector=(1.0, 0.0, 0.0, 0.0),
            GVector=(0.0, 1.0, 0.0, 0.0),
            BVector=(0.0, 0.0, 1.0, 0.0),
            AVector=(0.0, 0.0, 0.0, 1.0),
            biasVector=(0.0, 0.0, 0.0, 0.0),
        )

    def test_colorMonochrome(self):
        img = drawBot.ImageObject()
        img.colorMonochrome(color=(0.6, 0.45, 0.3, 1.0), intensity=1.0)

    def test_colorPolynomial(self):
        img = drawBot.ImageObject()
        img.colorPolynomial(
            redCoefficients=(0.0, 1.0, 0.0, 0.0),
            greenCoefficients=(0.0, 1.0, 0.0, 0.0),
            blueCoefficients=(0.0, 1.0, 0.0, 0.0),
            alphaCoefficients=(0.0, 1.0, 0.0, 0.0),
        )

    def test_colorPosterize(self):
        img = drawBot.ImageObject()
        img.colorPosterize(levels=6.0)

    def test_colorThreshold(self):
        img = drawBot.ImageObject()
        img.colorThreshold(threshold=0.5)

    def test_colorThresholdOtsu(self):
        img = drawBot.ImageObject()
        img.colorThresholdOtsu()

    def test_columnAverage(self):
        img = drawBot.ImageObject()
        img.columnAverage(extent=(0.0, 0.0, 640.0, 80.0))

    def test_comicEffect(self):
        img = drawBot.ImageObject()
        img.comicEffect()

    def test_constantColorGenerator(self):
        img = drawBot.ImageObject()
        img.constantColorGenerator(size=(100, 100), color=(1.0, 0.0, 0.0, 1.0))

    def test_convertLabToRGB(self):
        img = drawBot.ImageObject()
        img.convertLabToRGB(normalize=False)

    def test_convertRGBtoLab(self):
        img = drawBot.ImageObject()
        img.convertRGBtoLab(normalize=False)

    def test_convolution3X3(self):
        img = drawBot.ImageObject()
        img.convolution3X3(weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias=0.0)

    def test_convolution5X5(self):
        img = drawBot.ImageObject()
        img.convolution5X5(
            weights=(
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
            bias=0.0,
        )

    def test_convolution7X7(self):
        img = drawBot.ImageObject()
        img.convolution7X7(
            weights=(
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
            bias=0.0,
        )

    def test_convolution9Horizontal(self):
        img = drawBot.ImageObject()
        img.convolution9Horizontal(weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias=0.0)

    def test_convolution9Vertical(self):
        img = drawBot.ImageObject()
        img.convolution9Vertical(weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias=0.0)

    def test_convolutionRGB3X3(self):
        img = drawBot.ImageObject()
        img.convolutionRGB3X3(weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias=0.0)

    def test_convolutionRGB5X5(self):
        img = drawBot.ImageObject()
        img.convolutionRGB5X5(
            weights=(
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
            bias=0.0,
        )

    def test_convolutionRGB7X7(self):
        img = drawBot.ImageObject()
        img.convolutionRGB7X7(
            weights=(
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
            bias=0.0,
        )

    def test_convolutionRGB9Horizontal(self):
        img = drawBot.ImageObject()
        img.convolutionRGB9Horizontal(weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias=0.0)

    def test_convolutionRGB9Vertical(self):
        img = drawBot.ImageObject()
        img.convolutionRGB9Vertical(weights=(0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias=0.0)

    def test_copyMachineTransition(self):
        img = drawBot.ImageObject()
        img.copyMachineTransition(
            targetImage=sampleImage,
            extent=(0.0, 0.0, 300.0, 300.0),
            color=(0.6, 1.0, 0.8, 1.0),
            time=0.0,
            angle=0.0,
            width=200.0,
            opacity=1.3,
        )

    def test_coreMLModelFilter(self):
        img = drawBot.ImageObject()
        img.coreMLModelFilter(model=None, headIndex=0.0, softmaxNormalization=False)

    def test_crop(self):
        img = drawBot.ImageObject()
        img.crop(
            rectangle=(-8.988465674311579e307, -8.988465674311579e307, 1.7976931348623157e308, 1.7976931348623157e308)
        )

    def test_crystallize(self):
        img = drawBot.ImageObject()
        img.crystallize(radius=20.0, center=(150.0, 150.0))

    def test_darkenBlendMode(self):
        img = drawBot.ImageObject()
        img.darkenBlendMode(backgroundImage=sampleImage)

    def test_depthBlurEffect(self):
        img = drawBot.ImageObject()
        img.depthBlurEffect(
            disparityImage=sampleImage,
            matteImage=sampleImage,
            hairImage=sampleImage,
            glassesImage=sampleImage,
            gainMap=sampleImage,
            focusRect=None,
            calibrationData=None,
            auxDataMetadata=None,
            shape=None,
            aperture=0.0,
            leftEyePositions=(-1.0, -1.0),
            rightEyePositions=(-1.0, -1.0),
            chinPositions=(-1.0, -1.0),
            nosePositions=(-1.0, -1.0),
            lumaNoiseScale=0.0,
            scaleFactor=1.0,
        )

    def test_depthOfField(self):
        img = drawBot.ImageObject()
        img.depthOfField(
            point0=(0.0, 300.0),
            point1=(300.0, 300.0),
            saturation=1.5,
            unsharpMaskRadius=2.5,
            unsharpMaskIntensity=0.5,
            radius=6.0,
        )

    def test_depthToDisparity(self):
        img = drawBot.ImageObject()
        img.depthToDisparity()

    def test_differenceBlendMode(self):
        img = drawBot.ImageObject()
        img.differenceBlendMode(backgroundImage=sampleImage)

    def test_discBlur(self):
        img = drawBot.ImageObject()
        img.discBlur(radius=8.0)

    def test_disintegrateWithMaskTransition(self):
        img = drawBot.ImageObject()
        img.disintegrateWithMaskTransition(
            targetImage=sampleImage,
            maskImage=sampleImage,
            time=0.0,
            shadowRadius=8.0,
            shadowDensity=0.65,
            shadowOffset=(0.0, -10.0),
        )

    def test_disparityToDepth(self):
        img = drawBot.ImageObject()
        img.disparityToDepth()

    def test_displacementDistortion(self):
        img = drawBot.ImageObject()
        img.displacementDistortion(displacementImage=sampleImage, scale=50.0)

    def test_dissolveTransition(self):
        img = drawBot.ImageObject()
        img.dissolveTransition(targetImage=sampleImage, time=0.0)

    def test_dither(self):
        img = drawBot.ImageObject()
        img.dither(intensity=0.1)

    def test_divideBlendMode(self):
        img = drawBot.ImageObject()
        img.divideBlendMode(backgroundImage=sampleImage)

    def test_documentEnhancer(self):
        img = drawBot.ImageObject()
        img.documentEnhancer(amount=1.0)

    def test_dotScreen(self):
        img = drawBot.ImageObject()
        img.dotScreen(center=(150.0, 150.0), angle=0.0, width=6.0, sharpness=0.7)

    def test_droste(self):
        img = drawBot.ImageObject()
        img.droste(
            insetPoint0=(200.0, 200.0), insetPoint1=(400.0, 400.0), strands=1.0, periodicity=1.0, rotation=0.0, zoom=1.0
        )

    def test_edgePreserveUpsampleFilter(self):
        img = drawBot.ImageObject()
        img.edgePreserveUpsampleFilter(smallImage=sampleImage, spatialSigma=3.0, lumaSigma=0.15)

    def test_edges(self):
        img = drawBot.ImageObject()
        img.edges(intensity=1.0)

    def test_edgeWork(self):
        img = drawBot.ImageObject()
        img.edgeWork(radius=3.0)

    def test_eightfoldReflectedTile(self):
        img = drawBot.ImageObject()
        img.eightfoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)

    def test_exclusionBlendMode(self):
        img = drawBot.ImageObject()
        img.exclusionBlendMode(backgroundImage=sampleImage)

    def test_exposureAdjust(self):
        img = drawBot.ImageObject()
        img.exposureAdjust(EV=0.0)

    def test_falseColor(self):
        img = drawBot.ImageObject()
        img.falseColor(color0=(0.3, 0.0, 0.0, 1.0), color1=(1.0, 0.9, 0.8, 1.0))

    def test_flashTransition(self):
        img = drawBot.ImageObject()
        img.flashTransition(
            targetImage=sampleImage,
            center=(150.0, 150.0),
            extent=(0.0, 0.0, 300.0, 300.0),
            color=(1.0, 0.8, 0.6, 1.0),
            time=0.0,
            maxStriationRadius=2.58,
            striationStrength=0.5,
            striationContrast=1.375,
            fadeThreshold=0.85,
        )

    def test_fourfoldReflectedTile(self):
        img = drawBot.ImageObject()
        img.fourfoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0, acuteAngle=1.5707963267948966)

    def test_fourfoldRotatedTile(self):
        img = drawBot.ImageObject()
        img.fourfoldRotatedTile(center=(150.0, 150.0), angle=0.0, width=100.0)

    def test_fourfoldTranslatedTile(self):
        img = drawBot.ImageObject()
        img.fourfoldTranslatedTile(center=(150.0, 150.0), angle=0.0, width=100.0, acuteAngle=1.5707963267948966)

    def test_gaborGradients(self):
        img = drawBot.ImageObject()
        img.gaborGradients()

    def test_gammaAdjust(self):
        img = drawBot.ImageObject()
        img.gammaAdjust(power=1.0)

    def test_gaussianBlur(self):
        img = drawBot.ImageObject()
        img.gaussianBlur(radius=10.0)

    def test_gaussianGradient(self):
        img = drawBot.ImageObject()
        img.gaussianGradient(
            size=(100, 100),
            center=(150.0, 150.0),
            color0=(1.0, 1.0, 1.0, 1.0),
            color1=(0.0, 0.0, 0.0, 0.0),
            radius=300.0,
        )

    def test_glassDistortion(self):
        img = drawBot.ImageObject()
        img.glassDistortion(texture=sampleImage, center=(150.0, 150.0), scale=200.0)

    def test_glassLozenge(self):
        img = drawBot.ImageObject()
        img.glassLozenge(point0=(150.0, 150.0), point1=(350.0, 150.0), radius=100.0, refraction=1.7)

    def test_glideReflectedTile(self):
        img = drawBot.ImageObject()
        img.glideReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)

    def test_gloom(self):
        img = drawBot.ImageObject()
        img.gloom(radius=10.0, intensity=0.5)

    def test_guidedFilter(self):
        img = drawBot.ImageObject()
        img.guidedFilter(guideImage=sampleImage, radius=1.0, epsilon=0.0001)

    def test_hardLightBlendMode(self):
        img = drawBot.ImageObject()
        img.hardLightBlendMode(backgroundImage=sampleImage)

    def test_hatchedScreen(self):
        img = drawBot.ImageObject()
        img.hatchedScreen(center=(150.0, 150.0), angle=0.0, width=6.0, sharpness=0.7)

    def test_heightFieldFromMask(self):
        img = drawBot.ImageObject()
        img.heightFieldFromMask(radius=10.0)

    def test_hexagonalPixellate(self):
        img = drawBot.ImageObject()
        img.hexagonalPixellate(center=(150.0, 150.0), scale=8.0)

    def test_highlightShadowAdjust(self):
        img = drawBot.ImageObject()
        img.highlightShadowAdjust(radius=0.0, shadowAmount=0.0, highlightAmount=1.0)

    def test_histogramDisplayFilter(self):
        img = drawBot.ImageObject()
        img.histogramDisplayFilter(height=100.0, highLimit=1.0, lowLimit=0.0)

    def test_holeDistortion(self):
        img = drawBot.ImageObject()
        img.holeDistortion(center=(150.0, 150.0), radius=150.0)

    def test_hueAdjust(self):
        img = drawBot.ImageObject()
        img.hueAdjust(angle=0.0)

    def test_hueBlendMode(self):
        img = drawBot.ImageObject()
        img.hueBlendMode(backgroundImage=sampleImage)

    def test_hueSaturationValueGradient(self):
        img = drawBot.ImageObject()
        img.hueSaturationValueGradient(value=1.0, radius=300.0, softness=1.0, dither=1.0, colorSpace=None)

    def test_kaleidoscope(self):
        img = drawBot.ImageObject()
        img.kaleidoscope(count=6.0, center=(150.0, 150.0), angle=0.0)

    def test_keystoneCorrectionCombined(self):
        img = drawBot.ImageObject()
        img.keystoneCorrectionCombined(
            topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), focalLength=28.0
        )

    def test_keystoneCorrectionHorizontal(self):
        img = drawBot.ImageObject()
        img.keystoneCorrectionHorizontal(
            topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), focalLength=28.0
        )

    def test_keystoneCorrectionVertical(self):
        img = drawBot.ImageObject()
        img.keystoneCorrectionVertical(
            topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), focalLength=28.0
        )

    def test_KMeans(self):
        img = drawBot.ImageObject()
        img.KMeans(means=None, extent=(0.0, 0.0, 640.0, 80.0), count=8.0, passes=5.0, perceptual=False)

    def test_labDeltaE(self):
        img = drawBot.ImageObject()
        img.labDeltaE(image2=None)

    def test_lanczosScaleTransform(self):
        img = drawBot.ImageObject()
        img.lanczosScaleTransform(scale=1.0, aspectRatio=1.0)

    def test_lenticularHaloGenerator(self):
        img = drawBot.ImageObject()
        img.lenticularHaloGenerator(
            size=(100, 100),
            center=(150.0, 150.0),
            color=(1.0, 0.9, 0.8, 1.0),
            haloRadius=70.0,
            haloWidth=87.0,
            haloOverlap=0.77,
            striationStrength=0.5,
            striationContrast=1.0,
            time=0.0,
        )

    def test_lightenBlendMode(self):
        img = drawBot.ImageObject()
        img.lightenBlendMode(backgroundImage=sampleImage)

    def test_lightTunnel(self):
        img = drawBot.ImageObject()
        img.lightTunnel(center=(150.0, 150.0), rotation=0.0, radius=100.0)

    def test_linearBurnBlendMode(self):
        img = drawBot.ImageObject()
        img.linearBurnBlendMode(backgroundImage=sampleImage)

    def test_linearDodgeBlendMode(self):
        img = drawBot.ImageObject()
        img.linearDodgeBlendMode(backgroundImage=sampleImage)

    def test_linearGradient(self):
        img = drawBot.ImageObject()
        img.linearGradient(
            size=(100, 100),
            point0=(0.0, 0.0),
            point1=(200.0, 200.0),
            color0=(1.0, 1.0, 1.0, 1.0),
            color1=(0.0, 0.0, 0.0, 1.0),
        )

    def test_linearLightBlendMode(self):
        img = drawBot.ImageObject()
        img.linearLightBlendMode(backgroundImage=sampleImage)

    def test_linearToSRGBToneCurve(self):
        img = drawBot.ImageObject()
        img.linearToSRGBToneCurve()

    def test_lineOverlay(self):
        img = drawBot.ImageObject()
        img.lineOverlay(NRNoiseLevel=0.07, NRSharpness=0.71, edgeIntensity=1.0, threshold=0.1, contrast=50.0)

    def test_lineScreen(self):
        img = drawBot.ImageObject()
        img.lineScreen(center=(150.0, 150.0), angle=0.0, width=6.0, sharpness=0.7)

    def test_luminosityBlendMode(self):
        img = drawBot.ImageObject()
        img.luminosityBlendMode(backgroundImage=sampleImage)

    def test_maskedVariableBlur(self):
        img = drawBot.ImageObject()
        img.maskedVariableBlur(mask=sampleImage, radius=5.0)

    def test_maskToAlpha(self):
        img = drawBot.ImageObject()
        img.maskToAlpha()

    def test_maximumComponent(self):
        img = drawBot.ImageObject()
        img.maximumComponent()

    def test_maximumCompositing(self):
        img = drawBot.ImageObject()
        img.maximumCompositing(backgroundImage=sampleImage)

    def test_meshGenerator(self):
        img = drawBot.ImageObject()
        img.meshGenerator(size=(100, 100), mesh=None, width=1.5, color=(1.0, 1.0, 1.0, 1.0))

    def test_minimumComponent(self):
        img = drawBot.ImageObject()
        img.minimumComponent()

    def test_minimumCompositing(self):
        img = drawBot.ImageObject()
        img.minimumCompositing(backgroundImage=sampleImage)

    def test_mix(self):
        img = drawBot.ImageObject()
        img.mix(backgroundImage=sampleImage, amount=1.0)

    def test_modTransition(self):
        img = drawBot.ImageObject()
        img.modTransition(
            targetImage=sampleImage, center=(150.0, 150.0), time=0.0, angle=2.0, radius=150.0, compression=300.0
        )

    def test_morphologyGradient(self):
        img = drawBot.ImageObject()
        img.morphologyGradient(radius=5.0)

    def test_morphologyMaximum(self):
        img = drawBot.ImageObject()
        img.morphologyMaximum(radius=0.0)

    def test_morphologyMinimum(self):
        img = drawBot.ImageObject()
        img.morphologyMinimum(radius=0.0)

    def test_morphologyRectangleMaximum(self):
        img = drawBot.ImageObject()
        img.morphologyRectangleMaximum(width=5.0, height=5.0)

    def test_morphologyRectangleMinimum(self):
        img = drawBot.ImageObject()
        img.morphologyRectangleMinimum(width=5.0, height=5.0)

    def test_motionBlur(self):
        img = drawBot.ImageObject()
        img.motionBlur(radius=20.0, angle=0.0)

    def test_multiplyBlendMode(self):
        img = drawBot.ImageObject()
        img.multiplyBlendMode(backgroundImage=sampleImage)

    def test_multiplyCompositing(self):
        img = drawBot.ImageObject()
        img.multiplyCompositing(backgroundImage=sampleImage)

    def test_ninePartStretched(self):
        img = drawBot.ImageObject()
        img.ninePartStretched(breakpoint0=(50.0, 50.0), breakpoint1=(150.0, 150.0), growAmount=(100.0, 100.0))

    def test_ninePartTiled(self):
        img = drawBot.ImageObject()
        img.ninePartTiled(
            breakpoint0=(50.0, 50.0), breakpoint1=(150.0, 150.0), growAmount=(100.0, 100.0), flipYTiles=True
        )

    def test_noiseReduction(self):
        img = drawBot.ImageObject()
        img.noiseReduction(noiseLevel=0.02, sharpness=0.4)

    def test_opTile(self):
        img = drawBot.ImageObject()
        img.opTile(center=(150.0, 150.0), scale=2.8, angle=0.0, width=65.0)

    def test_overlayBlendMode(self):
        img = drawBot.ImageObject()
        img.overlayBlendMode(backgroundImage=sampleImage)

    def test_pageCurlTransition(self):
        img = drawBot.ImageObject()
        img.pageCurlTransition(
            targetImage=sampleImage,
            backsideImage=sampleImage,
            shadingImage=sampleImage,
            extent=(0.0, 0.0, 300.0, 300.0),
            time=0.0,
            angle=0.0,
            radius=100.0,
        )

    def test_pageCurlWithShadowTransition(self):
        img = drawBot.ImageObject()
        img.pageCurlWithShadowTransition(
            targetImage=sampleImage,
            backsideImage=sampleImage,
            extent=(0.0, 0.0, 0.0, 0.0),
            time=0.0,
            angle=0.0,
            radius=100.0,
            shadowSize=0.5,
            shadowAmount=0.7,
            shadowExtent=(0.0, 0.0, 0.0, 0.0),
        )

    def test_paletteCentroid(self):
        img = drawBot.ImageObject()
        img.paletteCentroid(paletteImage=sampleImage, perceptual=False)

    def test_palettize(self):
        img = drawBot.ImageObject()
        img.palettize(paletteImage=sampleImage, perceptual=False)

    def test_parallelogramTile(self):
        img = drawBot.ImageObject()
        img.parallelogramTile(center=(150.0, 150.0), angle=0.0, acuteAngle=1.5707963267948966, width=100.0)

    def test_PDF417BarcodeGenerator(self):
        img = drawBot.ImageObject()
        img.PDF417BarcodeGenerator(
            size=(100, 100),
            message=b"Hello World",
            minWidth=None,
            maxWidth=None,
            minHeight=None,
            maxHeight=None,
            dataColumns=None,
            rows=None,
            preferredAspectRatio=None,
            compactionMode=None,
            compactStyle=None,
            correctionLevel=None,
            alwaysSpecifyCompaction=None,
        )

    def test_personSegmentation(self):
        img = drawBot.ImageObject()
        img.personSegmentation(qualityLevel=0.0)

    def test_perspectiveCorrection(self):
        img = drawBot.ImageObject()
        img.perspectiveCorrection(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2), crop=True)

    def test_perspectiveRotate(self):
        img = drawBot.ImageObject()
        img.perspectiveRotate(focalLength=28.0, pitch=0.0, yaw=0.0, roll=0.0)

    def test_perspectiveTile(self):
        img = drawBot.ImageObject()
        img.perspectiveTile(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2))

    def test_perspectiveTransform(self):
        img = drawBot.ImageObject()
        img.perspectiveTransform(topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2))

    def test_perspectiveTransformWithExtent(self):
        img = drawBot.ImageObject()
        img.perspectiveTransformWithExtent(
            extent=(0.0, 0.0, 300.0, 300.0), topLeft=(2, 2), topRight=(2, 2), bottomRight=(2, 2), bottomLeft=(2, 2)
        )

    def test_photoEffectChrome(self):
        img = drawBot.ImageObject()
        img.photoEffectChrome(extrapolate=False)

    def test_photoEffectFade(self):
        img = drawBot.ImageObject()
        img.photoEffectFade(extrapolate=False)

    def test_photoEffectInstant(self):
        img = drawBot.ImageObject()
        img.photoEffectInstant(extrapolate=False)

    def test_photoEffectMono(self):
        img = drawBot.ImageObject()
        img.photoEffectMono(extrapolate=False)

    def test_photoEffectNoir(self):
        img = drawBot.ImageObject()
        img.photoEffectNoir(extrapolate=False)

    def test_photoEffectProcess(self):
        img = drawBot.ImageObject()
        img.photoEffectProcess(extrapolate=False)

    def test_photoEffectTonal(self):
        img = drawBot.ImageObject()
        img.photoEffectTonal(extrapolate=False)

    def test_photoEffectTransfer(self):
        img = drawBot.ImageObject()
        img.photoEffectTransfer(extrapolate=False)

    def test_pinchDistortion(self):
        img = drawBot.ImageObject()
        img.pinchDistortion(center=(150.0, 150.0), radius=300.0, scale=0.5)

    def test_pinLightBlendMode(self):
        img = drawBot.ImageObject()
        img.pinLightBlendMode(backgroundImage=sampleImage)

    def test_pixellate(self):
        img = drawBot.ImageObject()
        img.pixellate(center=(150.0, 150.0), scale=8.0)

    def test_pointillize(self):
        img = drawBot.ImageObject()
        img.pointillize(radius=20.0, center=(150.0, 150.0))

    def test_QRCodeGenerator(self):
        img = drawBot.ImageObject()
        img.QRCodeGenerator(size=(100, 100), message=b"Hello World", correctionLevel="M")

    def test_radialGradient(self):
        img = drawBot.ImageObject()
        img.radialGradient(
            size=(100, 100),
            center=(150.0, 150.0),
            radius0=5.0,
            radius1=100.0,
            color0=(1.0, 1.0, 1.0, 1.0),
            color1=(0.0, 0.0, 0.0, 1.0),
        )

    def test_randomGenerator(self):
        img = drawBot.ImageObject()
        img.randomGenerator(size=(100, 100))

    def test_rippleTransition(self):
        img = drawBot.ImageObject()
        img.rippleTransition(
            targetImage=sampleImage,
            shadingImage=sampleImage,
            center=(150.0, 150.0),
            extent=(0.0, 0.0, 300.0, 300.0),
            time=0.0,
            width=100.0,
            scale=50.0,
        )

    def test_roundedRectangleGenerator(self):
        img = drawBot.ImageObject()
        img.roundedRectangleGenerator(
            size=(100, 100), extent=(0.0, 0.0, 100.0, 100.0), radius=10.0, color=(1.0, 1.0, 1.0, 1.0)
        )

    def test_roundedRectangleStrokeGenerator(self):
        img = drawBot.ImageObject()
        img.roundedRectangleStrokeGenerator(
            size=(100, 100), extent=(0.0, 0.0, 100.0, 100.0), radius=10.0, color=(1.0, 1.0, 1.0, 1.0), width=10.0
        )

    def test_rowAverage(self):
        img = drawBot.ImageObject()
        img.rowAverage(extent=(0.0, 0.0, 640.0, 80.0))

    def test_saliencyMapFilter(self):
        img = drawBot.ImageObject()
        img.saliencyMapFilter()

    def test_sampleNearest(self):
        img = drawBot.ImageObject()
        img.sampleNearest()

    def test_saturationBlendMode(self):
        img = drawBot.ImageObject()
        img.saturationBlendMode(backgroundImage=sampleImage)

    def test_screenBlendMode(self):
        img = drawBot.ImageObject()
        img.screenBlendMode(backgroundImage=sampleImage)

    def test_sepiaTone(self):
        img = drawBot.ImageObject()
        img.sepiaTone(intensity=1.0)

    def test_shadedMaterial(self):
        img = drawBot.ImageObject()
        img.shadedMaterial(shadingImage=sampleImage, scale=10.0)

    def test_sharpenLuminance(self):
        img = drawBot.ImageObject()
        img.sharpenLuminance(sharpness=0.4, radius=1.69)

    def test_sixfoldReflectedTile(self):
        img = drawBot.ImageObject()
        img.sixfoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)

    def test_sixfoldRotatedTile(self):
        img = drawBot.ImageObject()
        img.sixfoldRotatedTile(center=(150.0, 150.0), angle=0.0, width=100.0)

    def test_smoothLinearGradient(self):
        img = drawBot.ImageObject()
        img.smoothLinearGradient(
            size=(100, 100),
            point0=(0.0, 0.0),
            point1=(200.0, 200.0),
            color0=(1.0, 1.0, 1.0, 1.0),
            color1=(0.0, 0.0, 0.0, 1.0),
        )

    def test_sobelGradients(self):
        img = drawBot.ImageObject()
        img.sobelGradients()

    def test_softLightBlendMode(self):
        img = drawBot.ImageObject()
        img.softLightBlendMode(backgroundImage=sampleImage)

    def test_sourceAtopCompositing(self):
        img = drawBot.ImageObject()
        img.sourceAtopCompositing(backgroundImage=sampleImage)

    def test_sourceInCompositing(self):
        img = drawBot.ImageObject()
        img.sourceInCompositing(backgroundImage=sampleImage)

    def test_sourceOutCompositing(self):
        img = drawBot.ImageObject()
        img.sourceOutCompositing(backgroundImage=sampleImage)

    def test_sourceOverCompositing(self):
        img = drawBot.ImageObject()
        img.sourceOverCompositing(backgroundImage=sampleImage)

    def test_spotColor(self):
        img = drawBot.ImageObject()
        img.spotColor(
            centerColor1=(0.0784, 0.0627, 0.0706, 1.0),
            replacementColor1=(0.4392, 0.1922, 0.1961, 1.0),
            closeness1=0.22,
            contrast1=0.98,
            centerColor2=(0.5255, 0.3059, 0.3451, 1.0),
            replacementColor2=(0.9137, 0.5608, 0.5059, 1.0),
            closeness2=0.15,
            contrast2=0.98,
            centerColor3=(0.9216, 0.4549, 0.3333, 1.0),
            replacementColor3=(0.9098, 0.7529, 0.6078, 1.0),
            closeness3=0.5,
            contrast3=0.99,
        )

    def test_spotLight(self):
        img = drawBot.ImageObject()
        img.spotLight(
            lightPosition=(400.0, 600.0, 150.0),
            lightPointsAt=(200.0, 200.0, 0.0),
            brightness=3.0,
            concentration=0.1,
            color=(1.0, 1.0, 1.0, 1.0),
        )

    def test_SRGBToneCurveToLinear(self):
        img = drawBot.ImageObject()
        img.SRGBToneCurveToLinear()

    def test_starShineGenerator(self):
        img = drawBot.ImageObject()
        img.starShineGenerator(
            size=(100, 100),
            center=(150.0, 150.0),
            color=(1.0, 0.8, 0.6, 1.0),
            radius=50.0,
            crossScale=15.0,
            crossAngle=0.6,
            crossOpacity=-2.0,
            crossWidth=2.5,
            epsilon=-2.0,
        )

    def test_straightenFilter(self):
        img = drawBot.ImageObject()
        img.straightenFilter(angle=0.0)

    def test_stretchCrop(self):
        img = drawBot.ImageObject()
        img.stretchCrop(size=(1280.0, 720.0), cropAmount=0.25, centerStretchAmount=0.25)

    def test_stripesGenerator(self):
        img = drawBot.ImageObject()
        img.stripesGenerator(
            size=(100, 100),
            center=(150.0, 150.0),
            color0=(1.0, 1.0, 1.0, 1.0),
            color1=(0.0, 0.0, 0.0, 1.0),
            width=80.0,
            sharpness=1.0,
        )

    def test_subtractBlendMode(self):
        img = drawBot.ImageObject()
        img.subtractBlendMode(backgroundImage=sampleImage)

    def test_sunbeamsGenerator(self):
        img = drawBot.ImageObject()
        img.sunbeamsGenerator(
            size=(100, 100),
            center=(150.0, 150.0),
            color=(1.0, 0.5, 0.0, 1.0),
            sunRadius=40.0,
            maxStriationRadius=2.58,
            striationStrength=0.5,
            striationContrast=1.375,
            time=0.0,
        )

    def test_swipeTransition(self):
        img = drawBot.ImageObject()
        img.swipeTransition(
            targetImage=sampleImage,
            extent=(0.0, 0.0, 300.0, 300.0),
            color=(1.0, 1.0, 1.0, 1.0),
            time=0.0,
            angle=0.0,
            width=300.0,
            opacity=0.0,
        )

    def test_temperatureAndTint(self):
        img = drawBot.ImageObject()
        img.temperatureAndTint(neutral=(6500.0, 0.0), targetNeutral=(6500.0, 0.0))

    def test_textImageGenerator(self):
        img = drawBot.ImageObject()
        img.textImageGenerator(
            size=(100, 100), text=fs, fontName="HelveticaNeue", fontSize=12.0, scaleFactor=1.0, padding=0.0
        )

    def test_thermal(self):
        img = drawBot.ImageObject()
        img.thermal()

    def test_toneCurve(self):
        img = drawBot.ImageObject()
        img.toneCurve(point0=(0.0, 0.0), point1=(0.25, 0.25), point2=(0.5, 0.5), point3=(0.75, 0.75), point4=(1.0, 1.0))

    def test_torusLensDistortion(self):
        img = drawBot.ImageObject()
        img.torusLensDistortion(center=(150.0, 150.0), radius=160.0, width=80.0, refraction=1.7)

    def test_triangleKaleidoscope(self):
        img = drawBot.ImageObject()
        img.triangleKaleidoscope(point=(150.0, 150.0), size=700.0, rotation=5.924285296593801, decay=0.85)

    def test_triangleTile(self):
        img = drawBot.ImageObject()
        img.triangleTile(center=(150.0, 150.0), angle=0.0, width=100.0)

    def test_twelvefoldReflectedTile(self):
        img = drawBot.ImageObject()
        img.twelvefoldReflectedTile(center=(150.0, 150.0), angle=0.0, width=100.0)

    def test_twirlDistortion(self):
        img = drawBot.ImageObject()
        img.twirlDistortion(center=(150.0, 150.0), radius=300.0, angle=3.141592653589793)

    def test_unsharpMask(self):
        img = drawBot.ImageObject()
        img.unsharpMask(radius=2.5, intensity=0.5)

    def test_vibrance(self):
        img = drawBot.ImageObject()
        img.vibrance(amount=0.0)

    def test_vignette(self):
        img = drawBot.ImageObject()
        img.vignette(intensity=0.0, radius=1.0)

    def test_vignetteEffect(self):
        img = drawBot.ImageObject()
        img.vignetteEffect(center=(150.0, 150.0), radius=150.0, intensity=1.0, falloff=0.5)

    def test_vividLightBlendMode(self):
        img = drawBot.ImageObject()
        img.vividLightBlendMode(backgroundImage=sampleImage)

    def test_vortexDistortion(self):
        img = drawBot.ImageObject()
        img.vortexDistortion(center=(150.0, 150.0), radius=300.0, angle=56.548667764616276)

    def test_whitePointAdjust(self):
        img = drawBot.ImageObject()
        img.whitePointAdjust(color=(1.0, 1.0, 1.0, 1.0))

    def test_XRay(self):
        img = drawBot.ImageObject()
        img.XRay()

    def test_zoomBlur(self):
        img = drawBot.ImageObject()
        img.zoomBlur(center=(150.0, 150.0), amount=20.0)


if __name__ == "__main__":
    sys.exit(unittest.main())
