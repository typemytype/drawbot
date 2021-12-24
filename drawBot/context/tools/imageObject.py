import AppKit
from math import radians
import os

from drawBot.misc import DrawBotError, optimizePath
from drawBot.context.imageContext import _makeBitmapImageRep


class ImageObject(object):

    """
    An image object with support for filters.

    Optional a `path` to an existing image can be provided.

    For more info see: `Core Image Filter Reference`_.

    .. _Core Image Filter Reference: https://developer.apple.com/library/mac/documentation/GraphicsImaging/Reference/CoreImageFilterReference/index.html
    """

    def __init__(self, path=None):
        self._filters = []
        if path is not None:
            self.open(path)

    def __del__(self):
        del self._filters
        if hasattr(self, "_source"):
            del self._source
        if hasattr(self, "_cachedImage"):
            del self._cachedImage

    def size(self):
        """
        Return the size of the image as a tuple.
        """
        (x, y), (w, h) = self._ciImage().extent()
        return w, h

    def offset(self):
        """
        Return the offset of the image, the origin point can change due to filters.
        """
        (x, y), (w, h) = self._ciImage().extent()
        return x, y

    def clearFilters(self):
        """
        Clear all filters.
        """
        self._filters = []

    def open(self, path):
        """
        Open an image with a given `path`.
        """
        if isinstance(path, AppKit.NSImage):
            im = path
        elif isinstance(path, (str, os.PathLike)):
            path = optimizePath(path)
            if path.startswith("http"):
                url = AppKit.NSURL.URLWithString_(path)
            else:
                if not os.path.exists(path):
                    raise DrawBotError("Image path '%s' does not exists." % path)
                url = AppKit.NSURL.fileURLWithPath_(path)
            im = AppKit.NSImage.alloc().initByReferencingURL_(url)
        else:
            raise DrawBotError("Cannot read image path '%s'." % path)
        rep = _makeBitmapImageRep(im)
        ciImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep)
        self._merge(ciImage, doCrop=True)

    def copy(self):
        """
        Return a copy.
        """
        new = self.__class__()
        new._filters = list(self._filters)
        if hasattr(self, "_source"):
            new._source = self._source.copy()
        if hasattr(self, "_cachedImage"):
            new._cachedImage = self._cachedImage.copy()
        return new

    def lockFocus(self):
        """
        Set focus on image.
        """
        from drawBot.drawBotDrawingTools import _drawBotDrawingTool
        # copy/save a state of the existing drawing tool
        self._originalTool = _drawBotDrawingTool._copy()
        # reset the existing one
        _drawBotDrawingTool._reset()
        # start a new drawing
        _drawBotDrawingTool.newDrawing()
        # set the size of the existing image, if there is one
        if hasattr(self, "_source"):
            w, h = self.size()
            _drawBotDrawingTool.size(w, h)

    def unlockFocus(self):
        """
        Set unlock focus on image.
        """
        from drawBot.drawBotDrawingTools import _drawBotDrawingTool, DrawBotDrawingTool
        # explicit tell the drawing is done
        _drawBotDrawingTool.endDrawing()
        # initiate a new drawing Tool
        self.imageDrawingTool = DrawBotDrawingTool()
        # reset the new drawing tool from the main drawing tool
        self.imageDrawingTool._reset(_drawBotDrawingTool)
        # reset the main drawing tool with a saved state of the tool
        _drawBotDrawingTool._reset(self._originalTool)
        # get the pdf data
        data = self.imageDrawingTool.pdfImage()
        # get the last page
        pageCount = data.pageCount()
        page = data.pageAtIndex_(pageCount-1)
        # create an image
        im = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
        # create an CIImage object
        rep = _makeBitmapImageRep(im)
        ciImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep)
        # merge it with the already set data, if there already an image
        self._merge(ciImage)

    def __enter__(self):
        self.lockFocus()
        return self

    def __exit__(self, type, value, traceback):
        self.unlockFocus()

    def _ciImage(self):
        """
        Return the CIImage object.
        """
        if not hasattr(self, "_cachedImage"):
            self._applyFilters()
        return self._cachedImage

    def _nsImage(self):
        """
        Return the NSImage object.
        """
        rep = AppKit.NSCIImageRep.imageRepWithCIImage_(self._ciImage())
        nsImage = AppKit.NSImage.alloc().initWithSize_(rep.size())
        nsImage.addRepresentation_(rep)
        return nsImage

    def _merge(self, ciImage, doCrop=False):
        """
        Merge with an other CIImage object by using the sourceOverCompositing filter.
        """
        if hasattr(self, "_source"):
            imObject = self.__class__()
            imObject._source = ciImage
            imObject.sourceOverCompositing(backgroundImage=self)
            if doCrop:
                (x, y), (w, h) = self._ciImage().extent()
                imObject.crop(rectangle=(x, y, w, h))
            ciImage = imObject._ciImage()
            if hasattr(self, "_cachedImage"):
                del self._cachedImage
        self._source = ciImage

    def _addFilter(self, filterDict):
        """
        Add an filter.
        """
        self._filters.append(filterDict)
        if hasattr(self, "_cachedImage"):
            del self._cachedImage

    def _applyFilters(self):
        """
        Apply all filters on the source image.
        Keep the _source image intact and store the result in a _cachedImage attribute.
        """
        if hasattr(self, "_source"):
            self._cachedImage = self._source.copy()
        for filterDict in self._filters:
            filterName = filterDict.get("name")
            ciFilter = AppKit.CIFilter.filterWithName_(filterName)
            ciFilter.setDefaults()

            for key, value in filterDict.get("attributes", {}).items():
                ciFilter.setValue_forKey_(value, key)

            if filterDict.get("isGenerator", False):
                w, h = filterDict["size"]
                dummy = AppKit.NSImage.alloc().initWithSize_((w, h))
                generator = ciFilter.valueForKey_("outputImage")
                dummy.lockFocus()
                ctx = AppKit.NSGraphicsContext.currentContext()
                ctx.setShouldAntialias_(False)
                ctx.setImageInterpolation_(AppKit.NSImageInterpolationNone)
                generator.drawAtPoint_fromRect_operation_fraction_((0, 0), ((0, 0), (w, h)), AppKit.NSCompositeCopy, 1)
                dummy.unlockFocus()
                rep = _makeBitmapImageRep(dummy)
                self._cachedImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep)
                del dummy
            elif hasattr(self, "_cachedImage"):
                ciFilter.setValue_forKey_(self._cachedImage, "inputImage")
                self._cachedImage = ciFilter.valueForKey_("outputImage")
        if not hasattr(self, "_cachedImage"):
            raise DrawBotError("Image does not contain any data. Draw into the image object first or set image data from a path.")

    # filters

    def boxBlur(self, radius=None):
        """
        Blurs an image using a box-shaped convolution kernel.

        Attributes: `radius` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIBoxBlur", attributes=attr)
        self._addFilter(filterDict)

    def discBlur(self, radius=None):
        """
        Blurs an image using a disc-shaped convolution kernel.

        Attributes: `radius` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIDiscBlur", attributes=attr)
        self._addFilter(filterDict)

    def gaussianBlur(self, radius=None):
        """
        Spreads source pixels by an amount specified by a Gaussian distribution.

        Attributes: `radius` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIGaussianBlur", attributes=attr)
        self._addFilter(filterDict)

    def maskedVariableBlur(self, mask=None, radius=None):
        """
        Blurs the source image according to the brightness levels in a mask image.

        Attributes: `mask` an Image object, `radius` a float.
        """
        attr = dict()
        if mask:
            attr["inputMask"] = mask._ciImage()
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIMaskedVariableBlur", attributes=attr)
        self._addFilter(filterDict)

    def motionBlur(self, radius=None, angle=None):
        """
        Blurs an image to simulate the effect of using a camera that moves a specified angle and distance while capturing the image.

        Attributes: `radius` a float, `angle` a float in degrees.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        if angle:
            attr["inputAngle"] = radians(angle)
        filterDict = dict(name="CIMotionBlur", attributes=attr)
        self._addFilter(filterDict)

    def noiseReduction(self, noiseLevel=None, sharpness=None):
        """
        Reduces noise using a threshold value to define what is considered noise.

        Attributes: `noiseLevel` a float, `sharpness` a float.
        """
        attr = dict()
        if noiseLevel:
            attr["inputNoiseLevel"] = noiseLevel
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CINoiseReduction", attributes=attr)
        self._addFilter(filterDict)

    def zoomBlur(self, center=None, amount=None):
        """
        Simulates the effect of zooming the camera while capturing the image.

        Attributes: `center` a tuple (x, y), `amount` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if amount:
            attr["inputAmount"] = amount
        filterDict = dict(name="CIZoomBlur", attributes=attr)
        self._addFilter(filterDict)

    def colorClamp(self, minComponents=None, maxComponents=None):
        """
        Modifies color values to keep them within a specified range.

        Attributes: `minComponents` a tuple (x, y, w, h), `maxComponents` a tuple (x, y, w, h).
        """
        attr = dict()
        if minComponents:
            attr["inputMinComponents"] = AppKit.CIVector.vectorWithValues_count_(minComponents, 4)
        if maxComponents:
            attr["inputMaxComponents"] = AppKit.CIVector.vectorWithValues_count_(maxComponents, 4)
        filterDict = dict(name="CIColorClamp", attributes=attr)
        self._addFilter(filterDict)

    def colorControls(self, saturation=None, brightness=None, contrast=None):
        """
        Adjusts saturation, brightness, and contrast values.

        Attributes: `saturation` a float, `brightness` a float, `contrast` a float.
        """
        attr = dict()
        if saturation:
            attr["inputSaturation"] = saturation
        if brightness:
            attr["inputBrightness"] = brightness
        if contrast:
            attr["inputContrast"] = contrast
        filterDict = dict(name="CIColorControls", attributes=attr)
        self._addFilter(filterDict)

    def colorMatrix(self, RVector=None, GVector=None, BVector=None, AVector=None, biasVector=None):
        """
        Multiplies source color values and adds a bias factor to each color component.

        Attributes: `RVector` a tuple (x, y, w, h), `GVector` a tuple (x, y, w, h), `BVector` a tuple (x, y, w, h), `AVector` a tuple (x, y, w, h), `biasVector` a tuple (x, y, w, h).
        """
        attr = dict()
        if RVector:
            attr["inputRVector"] = AppKit.CIVector.vectorWithValues_count_(RVector, 4)
        if GVector:
            attr["inputGVector"] = AppKit.CIVector.vectorWithValues_count_(GVector, 4)
        if BVector:
            attr["inputBVector"] = AppKit.CIVector.vectorWithValues_count_(BVector, 4)
        if AVector:
            attr["inputAVector"] = AppKit.CIVector.vectorWithValues_count_(AVector, 4)
        if biasVector:
            attr["inputBiasVector"] = AppKit.CIVector.vectorWithValues_count_(biasVector, 4)
        filterDict = dict(name="CIColorMatrix", attributes=attr)
        self._addFilter(filterDict)

    def colorPolynomial(self, redCoefficients=None, greenCoefficients=None, blueCoefficients=None, alphaCoefficients=None):
        """
        Modifies the pixel values in an image by applying a set of cubic polynomials.

        Attributes: `redCoefficients` a tuple (x, y, w, h), `greenCoefficients` a tuple (x, y, w, h), `blueCoefficients` a tuple (x, y, w, h), `alphaCoefficients` a tuple (x, y, w, h).
        """
        attr = dict()
        if redCoefficients:
            attr["inputRedCoefficients"] = AppKit.CIVector.vectorWithValues_count_(redCoefficients, 4)
        if greenCoefficients:
            attr["inputGreenCoefficients"] = AppKit.CIVector.vectorWithValues_count_(greenCoefficients, 4)
        if blueCoefficients:
            attr["inputBlueCoefficients"] = AppKit.CIVector.vectorWithValues_count_(blueCoefficients, 4)
        if alphaCoefficients:
            attr["inputAlphaCoefficients"] = AppKit.CIVector.vectorWithValues_count_(alphaCoefficients, 4)
        filterDict = dict(name="CIColorPolynomial", attributes=attr)
        self._addFilter(filterDict)

    def exposureAdjust(self, EV=None):
        """
        Adjusts the exposure setting for an image similar to the way you control exposure for a camera when you change the F-stop.

        Attributes: `EV` a float.
        """
        attr = dict()
        if EV:
            attr["inputEV"] = EV
        filterDict = dict(name="CIExposureAdjust", attributes=attr)
        self._addFilter(filterDict)

    def gammaAdjust(self, power=None):
        """
        Adjusts midtone brightness.

        Attributes: `power` a float.
        """
        attr = dict()
        if power:
            attr["inputPower"] = power
        filterDict = dict(name="CIGammaAdjust", attributes=attr)
        self._addFilter(filterDict)

    def hueAdjust(self, angle=None):
        """
        Changes the overall hue, or tint, of the source pixels.

        Attributes: `angle` a float in degrees.
        """
        attr = dict()
        if angle:
            attr["inputAngle"] = radians(angle)
        filterDict = dict(name="CIHueAdjust", attributes=attr)
        self._addFilter(filterDict)

    def linearToSRGBToneCurve(self):
        """
        Maps color intensity from a linear gamma curve to the sRGB color space.
        """
        attr = dict()
        filterDict = dict(name="CILinearToSRGBToneCurve", attributes=attr)
        self._addFilter(filterDict)

    def SRGBToneCurveToLinear(self):
        """
        Maps color intensity from the sRGB color space to a linear gamma curve.
        """
        attr = dict()
        filterDict = dict(name="CISRGBToneCurveToLinear", attributes=attr)
        self._addFilter(filterDict)

    def temperatureAndTint(self, neutral=None, targetNeutral=None):
        """
        Adapts the reference white point for an image.

        Attributes: `neutral` a tuple, `targetNeutral` a tuple.
        """
        attr = dict()
        if neutral:
            attr["inputNeutral"] = AppKit.CIVector.vectorWithValues_count_(neutral, 2)
        if targetNeutral:
            attr["inputTargetNeutral"] = AppKit.CIVector.vectorWithValues_count_(targetNeutral, 2)
        filterDict = dict(name="CITemperatureAndTint", attributes=attr)
        self._addFilter(filterDict)

    def toneCurve(self, point0=None, point1=None, point2=None, point3=None, point4=None):
        """
        Adjusts tone response of the R, G, and B channels of an image.

        Attributes: `point0` a tuple (x, y), `point1` a tuple (x, y), `point2` a tuple (x, y), `point3` a tuple (x, y), `point4` a tuple (x, y).
        """
        attr = dict()
        if point0:
            attr["inputPoint0"] = AppKit.CIVector.vectorWithValues_count_(point0, 2)
        if point1:
            attr["inputPoint1"] = AppKit.CIVector.vectorWithValues_count_(point1, 2)
        if point2:
            attr["inputPoint2"] = AppKit.CIVector.vectorWithValues_count_(point2, 2)
        if point3:
            attr["inputPoint3"] = AppKit.CIVector.vectorWithValues_count_(point3, 2)
        if point4:
            attr["inputPoint4"] = AppKit.CIVector.vectorWithValues_count_(point4, 2)
        filterDict = dict(name="CIToneCurve", attributes=attr)
        self._addFilter(filterDict)

    def vibrance(self, amount=None):
        """
        Adjusts the saturation of an image while keeping pleasing skin tones.

        Attributes: `amount` a float.
        """
        attr = dict()
        if amount:
            attr["inputAmount"] = amount
        filterDict = dict(name="CIVibrance", attributes=attr)
        self._addFilter(filterDict)

    def whitePointAdjust(self, color=None):
        """
        Adjusts the reference white point for an image and maps all colors in the source using the new reference.

        Attributes: `color` RGBA tuple Color (r, g, b, a).
        """
        attr = dict()
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        filterDict = dict(name="CIWhitePointAdjust", attributes=attr)
        self._addFilter(filterDict)

    def colorCrossPolynomial(self, redCoefficients=None, greenCoefficients=None, blueCoefficients=None):
        """
        Modifies the pixel values in an image by applying a set of polynomial cross-products.

        Attributes: `redCoefficients` a tuple (x, y, w, h), `greenCoefficients` a tuple (x, y, w, h), `blueCoefficients` a tuple (x, y, w, h).
        """
        attr = dict()
        if redCoefficients:
            attr["inputRedCoefficients"] = AppKit.CIVector.vectorWithValues_count_(redCoefficients, 4)
        if greenCoefficients:
            attr["inputGreenCoefficients"] = AppKit.CIVector.vectorWithValues_count_(greenCoefficients, 4)
        if blueCoefficients:
            attr["inputBlueCoefficients"] = AppKit.CIVector.vectorWithValues_count_(blueCoefficients, 4)
        filterDict = dict(name="CIColorCrossPolynomial", attributes=attr)
        self._addFilter(filterDict)

    def colorInvert(self):
        """
        Inverts the colors in an image.
        """
        attr = dict()
        filterDict = dict(name="CIColorInvert", attributes=attr)
        self._addFilter(filterDict)

    def colorMap(self, gradientImage=None):
        """
        Performs a nonlinear transformation of source color values using mapping values provided in a table.

        Attributes: `gradientImage` an Image object.
        """
        attr = dict()
        if gradientImage:
            attr["inputGradientImage"] = gradientImage._ciImage()
        filterDict = dict(name="CIColorMap", attributes=attr)
        self._addFilter(filterDict)

    def colorMonochrome(self, color=None, intensity=None):
        """
        Remaps colors so they fall within shades of a single color.

        Attributes: `color` RGBA tuple Color (r, g, b, a), `intensity` a float.
        """
        attr = dict()
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        if intensity:
            attr["inputIntensity"] = intensity
        filterDict = dict(name="CIColorMonochrome", attributes=attr)
        self._addFilter(filterDict)

    def colorPosterize(self, levels=None):
        """
        Remaps red, green, and blue color components to the number of brightness values you specify for each color component.

        Attributes: `levels` a float.
        """
        attr = dict()
        if levels:
            attr["inputLevels"] = levels
        filterDict = dict(name="CIColorPosterize", attributes=attr)
        self._addFilter(filterDict)

    def falseColor(self, color0=None, color1=None):
        """
        Maps luminance to a color ramp of two colors.

        Attributes: `color0` RGBA tuple Color (r, g, b, a), `color1` RGBA tuple Color (r, g, b, a).
        """
        attr = dict()
        if color0:
            attr["inputColor0"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3])
        if color1:
            attr["inputColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
        filterDict = dict(name="CIFalseColor", attributes=attr)
        self._addFilter(filterDict)

    def maskToAlpha(self):
        """
        Converts a grayscale image to a white image that is masked by alpha.
        """
        attr = dict()
        filterDict = dict(name="CIMaskToAlpha", attributes=attr)
        self._addFilter(filterDict)

    def maximumComponent(self):
        """
        Returns a grayscale image from max(r,g,b).
        """
        attr = dict()
        filterDict = dict(name="CIMaximumComponent", attributes=attr)
        self._addFilter(filterDict)

    def minimumComponent(self):
        """
        Returns a grayscale image from min(r,g,b).
        """
        attr = dict()
        filterDict = dict(name="CIMinimumComponent", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectChrome(self):
        """
        Applies a preconfigured set of effects that imitate vintage photography film with exaggerated color.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectChrome", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectFade(self):
        """
        Applies a preconfigured set of effects that imitate vintage photography film with diminished color.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectFade", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectInstant(self):
        """
        Applies a preconfigured set of effects that imitate vintage photography film with distorted colors.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectInstant", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectMono(self):
        """
        Applies a preconfigured set of effects that imitate black-and-white photography film with low contrast.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectMono", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectNoir(self):
        """
        Applies a preconfigured set of effects that imitate black-and-white photography film with exaggerated contrast.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectNoir", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectProcess(self):
        """
        Applies a preconfigured set of effects that imitate vintage photography film with emphasized cool colors.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectProcess", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectTonal(self):
        """
        Applies a preconfigured set of effects that imitate black-and-white photography film without significantly altering contrast.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectTonal", attributes=attr)
        self._addFilter(filterDict)

    def photoEffectTransfer(self):
        """
        Applies a preconfigured set of effects that imitate vintage photography film with emphasized warm colors.
        """
        attr = dict()
        filterDict = dict(name="CIPhotoEffectTransfer", attributes=attr)
        self._addFilter(filterDict)

    def sepiaTone(self, intensity=None):
        """
        Maps the colors of an image to various shades of brown.

        Attributes: `intensity` a float.
        """
        attr = dict()
        if intensity:
            attr["inputIntensity"] = intensity
        filterDict = dict(name="CISepiaTone", attributes=attr)
        self._addFilter(filterDict)

    def vignette(self, radius=None, intensity=None):
        """
        Reduces the brightness of an image at the periphery.

        Attributes: `radius` a float, `intensity` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        if intensity:
            attr["inputIntensity"] = intensity
        filterDict = dict(name="CIVignette", attributes=attr)
        self._addFilter(filterDict)

    def vignetteEffect(self, center=None, intensity=None, radius=None):
        """
        Modifies the brightness of an image around the periphery of a specified region.

        Attributes: `center` a tuple (x, y), `intensity` a float, `radius` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if intensity:
            attr["inputIntensity"] = intensity
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIVignetteEffect", attributes=attr)
        self._addFilter(filterDict)

    def additionCompositing(self, backgroundImage=None):
        """
        Adds color components to achieve a brightening effect.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIAdditionCompositing", attributes=attr)
        self._addFilter(filterDict)

    def colorBlendMode(self, backgroundImage=None):
        """
        Uses the luminance values of the background with the hue and saturation values of the source image.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIColorBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def colorBurnBlendMode(self, backgroundImage=None):
        """
        Darkens the background image samples to reflect the source image samples.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIColorBurnBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def colorDodgeBlendMode(self, backgroundImage=None):
        """
        Brightens the background image samples to reflect the source image samples.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIColorDodgeBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def darkenBlendMode(self, backgroundImage=None):
        """
        Creates composite image samples by choosing the darker samples (from either the source image or the background).

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIDarkenBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def differenceBlendMode(self, backgroundImage=None):
        """
        Subtracts either the source image sample color from the background image sample color, or the reverse, depending on which sample has the greater brightness value.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIDifferenceBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def divideBlendMode(self, backgroundImage=None):
        """
        Divides the background image sample color from the source image sample color.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIDivideBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def exclusionBlendMode(self, backgroundImage=None):
        """
        Produces an effect similar to that produced by the `differenceBlendMode` filter but with lower contrast.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIExclusionBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def hardLightBlendMode(self, backgroundImage=None):
        """
        Either multiplies or screens colors, depending on the source image sample color.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIHardLightBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def hueBlendMode(self, backgroundImage=None):
        """
        Uses the luminance and saturation values of the background image with the hue of the input image.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIHueBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def lightenBlendMode(self, backgroundImage=None):
        """
        Creates composite image samples by choosing the lighter samples (either from the source image or the background).

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CILightenBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def linearBurnBlendMode(self, backgroundImage=None):
        """
        Darkens the background image samples to reflect the source image samples while also increasing contrast.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CILinearBurnBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def linearDodgeBlendMode(self, backgroundImage=None):
        """
        Brightens the background image samples to reflect the source image samples while also increasing contrast.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CILinearDodgeBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def luminosityBlendMode(self, backgroundImage=None):
        """
        Uses the hue and saturation of the background image with the luminance of the input image.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CILuminosityBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def maximumCompositing(self, backgroundImage=None):
        """
        Computes the maximum value, by color component, of two input images and creates an output image using the maximum values.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIMaximumCompositing", attributes=attr)
        self._addFilter(filterDict)

    def minimumCompositing(self, backgroundImage=None):
        """
        Computes the minimum value, by color component, of two input images and creates an output image using the minimum values.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIMinimumCompositing", attributes=attr)
        self._addFilter(filterDict)

    def multiplyBlendMode(self, backgroundImage=None):
        """
        Multiplies the input image samples with the background image samples.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIMultiplyBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def multiplyCompositing(self, backgroundImage=None):
        """
        Multiplies the color component of two input images and creates an output image using the multiplied values.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIMultiplyCompositing", attributes=attr)
        self._addFilter(filterDict)

    def overlayBlendMode(self, backgroundImage=None):
        """
        Either multiplies or screens the input image samples with the background image samples, depending on the background color.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIOverlayBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def pinLightBlendMode(self, backgroundImage=None):
        """
        Conditionally replaces background image samples with source image samples depending on the brightness of the source image samples.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIPinLightBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def saturationBlendMode(self, backgroundImage=None):
        """
        Uses the luminance and hue values of the background image with the saturation of the input image.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CISaturationBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def screenBlendMode(self, backgroundImage=None):
        """
        Multiplies the inverse of the input image samples with the inverse of the background image samples.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CIScreenBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def softLightBlendMode(self, backgroundImage=None):
        """
        Either darkens or lightens colors, depending on the input image sample color.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CISoftLightBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def sourceAtopCompositing(self, backgroundImage=None):
        """
        Places the input image over the background image, then uses the luminance of the background image to determine what to show.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CISourceAtopCompositing", attributes=attr)
        self._addFilter(filterDict)

    def sourceInCompositing(self, backgroundImage=None):
        """
        Uses the background image to define what to leave in the input image, effectively cropping the input image.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CISourceInCompositing", attributes=attr)
        self._addFilter(filterDict)

    def sourceOutCompositing(self, backgroundImage=None):
        """
        Uses the background image to define what to take out of the input image.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CISourceOutCompositing", attributes=attr)
        self._addFilter(filterDict)

    def sourceOverCompositing(self, backgroundImage=None):
        """
        Places the input image over the input background image.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CISourceOverCompositing", attributes=attr)
        self._addFilter(filterDict)

    def subtractBlendMode(self, backgroundImage=None):
        """
        Subtracts the background image sample color from the source image sample color.

        Attributes: `backgroundImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        filterDict = dict(name="CISubtractBlendMode", attributes=attr)
        self._addFilter(filterDict)

    def bumpDistortion(self, center=None, radius=None, scale=None):
        """
        Creates a bump that originates at a specified point in the image.

        Attributes: `center` a tuple (x, y), `radius` a float, `scale` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIBumpDistortion", attributes=attr)
        self._addFilter(filterDict)

    def bumpDistortionLinear(self, center=None, radius=None, angle=None, scale=None):
        """
        Creates a concave or convex distortion that originates from a line in the image.

        Attributes: `center` a tuple (x, y), `radius` a float, `angle` a float in degrees, `scale` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        if angle:
            attr["inputAngle"] = radians(angle)
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIBumpDistortionLinear", attributes=attr)
        self._addFilter(filterDict)

    def circleSplashDistortion(self, center=None, radius=None):
        """
        Distorts the pixels starting at the circumference of a circle and emanating outward.

        Attributes: `center` a tuple (x, y), `radius` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CICircleSplashDistortion", attributes=attr)
        self._addFilter(filterDict)

    def circularWrap(self, center=None, radius=None, angle=None):
        """
        Wraps an image around a transparent circle.

        Attributes: `center` a tuple (x, y), `radius` a float, `angle` a float in degrees.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        if angle:
            attr["inputAngle"] = radians(angle)
        filterDict = dict(name="CICircularWrap", attributes=attr)
        self._addFilter(filterDict)

    def droste(self, insetPoint0=None, insetPoint1=None, strands=None, periodicity=None, rotation=None, zoom=None):
        """
        Recursively draws a portion of an image in imitation of an M. C. Escher drawing.

        Attributes: `insetPoint0` a tuple (x, y), `insetPoint1` a tuple (x, y), `strands` a float, `periodicity` a float, `rotation` a float, `zoom` a float.
        """
        attr = dict()
        if insetPoint0:
            attr["inputInsetPoint0"] = AppKit.CIVector.vectorWithValues_count_(insetPoint0, 2)
        if insetPoint1:
            attr["inputInsetPoint1"] = AppKit.CIVector.vectorWithValues_count_(insetPoint1, 2)
        if strands:
            attr["inputStrands"] = strands
        if periodicity:
            attr["inputPeriodicity"] = periodicity
        if rotation:
            attr["inputRotation"] = rotation
        if zoom:
            attr["inputZoom"] = zoom
        filterDict = dict(name="CIDroste", attributes=attr)
        self._addFilter(filterDict)

    def displacementDistortion(self, displacementImage=None, scale=None):
        """
        Applies the grayscale values of the second image to the first image.

        Attributes: `displacementImage` an Image object, `scale` a float.
        """
        attr = dict()
        if displacementImage:
            attr["inputDisplacementImage"] = displacementImage._ciImage()
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIDisplacementDistortion", attributes=attr)
        self._addFilter(filterDict)

    def glassDistortion(self, texture=None, center=None, scale=None):
        """
        Distorts an image by applying a glass-like texture.

        Attributes: `texture` an Image object, `center` a tuple (x, y), `scale` a float.
        """
        attr = dict()
        if texture:
            attr["inputTexture"] = texture._ciImage()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIGlassDistortion", attributes=attr)
        self._addFilter(filterDict)

    def glassLozenge(self, point0=None, point1=None, radius=None, refraction=None):
        """
        Creates a lozenge-shaped lens and distorts the portion of the image over which the lens is placed.

        Attributes: `point0` a tuple (x, y), `point1` a tuple (x, y), `radius` a float, `refraction` a float.
        """
        attr = dict()
        if point0:
            attr["inputPoint0"] = AppKit.CIVector.vectorWithValues_count_(point0, 2)
        if point1:
            attr["inputPoint1"] = AppKit.CIVector.vectorWithValues_count_(point1, 2)
        if radius:
            attr["inputRadius"] = radius
        if refraction:
            attr["inputRefraction"] = refraction
        filterDict = dict(name="CIGlassLozenge", attributes=attr)
        self._addFilter(filterDict)

    def holeDistortion(self, center=None, radius=None):
        """
        Creates a circular area that pushes the image pixels outward, distorting those pixels closest to the circle the most.

        Attributes: `center` a tuple (x, y), `radius` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIHoleDistortion", attributes=attr)
        self._addFilter(filterDict)

    def pinchDistortion(self, center=None, radius=None, scale=None):
        """
        Creates a rectangular area that pinches source pixels inward, distorting those pixels closest to the rectangle the most.

        Attributes: `center` a tuple (x, y), `radius` a float, `scale` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIPinchDistortion", attributes=attr)
        self._addFilter(filterDict)

    def stretchCrop(self, size=None, cropAmount=None, centerStretchAmount=None):
        """
        Distorts an image by stretching and or cropping it to fit a target size.

        Attributes: `size`, `cropAmount` a float, `centerStretchAmount` a float.
        """
        attr = dict()
        if size:
            attr["inputSize"] = size
        if cropAmount:
            attr["inputCropAmount"] = cropAmount
        if centerStretchAmount:
            attr["inputCenterStretchAmount"] = centerStretchAmount
        filterDict = dict(name="CIStretchCrop", attributes=attr)
        self._addFilter(filterDict)

    def torusLensDistortion(self, center=None, radius=None, width=None, refraction=None):
        """
        Creates a torus-shaped lens and distorts the portion of the image over which the lens is placed.

        Attributes: `center` a tuple (x, y), `radius` a float, `width` a float, `refraction` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        if width:
            attr["inputWidth"] = width
        if refraction:
            attr["inputRefraction"] = refraction
        filterDict = dict(name="CITorusLensDistortion", attributes=attr)
        self._addFilter(filterDict)

    def twirlDistortion(self, center=None, radius=None, angle=None):
        """
        Rotates pixels around a point to give a twirling effect.

        Attributes: `center` a tuple (x, y), `radius` a float, `angle` a float in degrees.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        if angle:
            attr["inputAngle"] = radians(angle)
        filterDict = dict(name="CITwirlDistortion", attributes=attr)
        self._addFilter(filterDict)

    def vortexDistortion(self, center=None, radius=None, angle=None):
        """
        Rotates pixels around a point to simulate a vortex.

        Attributes: `center` a tuple (x, y), `radius` a float, `angle` a float in degrees.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius:
            attr["inputRadius"] = radius
        if angle:
            attr["inputAngle"] = angle
        filterDict = dict(name="CIVortexDistortion", attributes=attr)
        self._addFilter(filterDict)

    def aztecCodeGenerator(self, size, message=None, correctionLevel=None, layers=None, compactStyle=None):
        """
        Generates an Aztec code (two-dimensional barcode) from input data.

        Attributes: `message` as bytes, `correctionLevel` a float, `layers` a float, `compactStyle` a bool.
        """
        attr = dict()
        if message:
            attr["inputMessage"] = AppKit.NSData.dataWithBytes_length_(message, len(message))
        if correctionLevel:
            attr["inputCorrectionLevel"] = correctionLevel
        if layers:
            attr["inputLayers"] = layers
        if compactStyle:
            attr["inputCompactStyle"] = compactStyle
        filterDict = dict(name="CIAztecCodeGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def QRCodeGenerator(self, size, message=None, correctionLevel=None):
        """
        Generates a Quick Response code (two-dimensional barcode) from input data.

        Attributes: `message` as bytes, `correctionLevel` a single letter string,
        options are: `'L'` (7%), `'M'` (15%), `'Q'` (25%) or `'H'` (30%).
        """
        attr = dict()
        if message:
            attr["inputMessage"] = AppKit.NSData.dataWithBytes_length_(message, len(message))
        if correctionLevel:
            assert correctionLevel in "LMQH", "'correctionLevel' must be either 'L', 'M', 'Q', 'H'"
            attr["inputCorrectionLevel"] = correctionLevel
        filterDict = dict(name="CIQRCodeGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def code128BarcodeGenerator(self, size, message=None, quietSpace=None):
        """
        Generates a Code 128 one-dimensional barcode from input data.

        Attributes: `message` a bytes, `quietSpace` a float.
        """
        attr = dict()
        if message:
            attr["inputMessage"] = AppKit.NSData.dataWithBytes_length_(message, len(message))
        if quietSpace:
            attr["inputQuietSpace"] = quietSpace
        filterDict = dict(name="CICode128BarcodeGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def checkerboardGenerator(self, size, center=None, color0=None, color1=None, width=None, sharpness=None):
        """
        Generates a checkerboard pattern.

        Attributes: `center` a tuple (x, y), `color0` RGBA tuple Color (r, g, b, a), `color1` RGBA tuple Color (r, g, b, a), `width` a float, `sharpness` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if color0:
            attr["inputColor0"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3])
        if color1:
            attr["inputColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
        if width:
            attr["inputWidth"] = width
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CICheckerboardGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def constantColorGenerator(self, size, color=None):
        """
        Generates a solid color.

        Attributes: `color` RGBA tuple Color (r, g, b, a).
        """
        attr = dict()
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        filterDict = dict(name="CIConstantColorGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def lenticularHaloGenerator(self, size, center=None, color=None, haloRadius=None, haloWidth=None, haloOverlap=None, striationStrength=None, striationContrast=None, time=None):
        """
        Simulates a lens flare.

        Attributes: `center` a tuple (x, y), `color` RGBA tuple Color (r, g, b, a), `haloRadius` a float, `haloWidth` a float, `haloOverlap` a float, `striationStrength` a float, `striationContrast` a float, `time` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        if haloRadius:
            attr["inputHaloRadius"] = haloRadius
        if haloWidth:
            attr["inputHaloWidth"] = haloWidth
        if haloOverlap:
            attr["inputHaloOverlap"] = haloOverlap
        if striationStrength:
            attr["inputStriationStrength"] = striationStrength
        if striationContrast:
            attr["inputStriationContrast"] = striationContrast
        if time:
            attr["inputTime"] = time
        filterDict = dict(name="CILenticularHaloGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def PDF417BarcodeGenerator(self, size, message=None, minWidth=None, maxWidth=None, minHeight=None, maxHeight=None, dataColumns=None, rows=None, preferredAspectRatio=None, compactionMode=None, compactStyle=None, correctionLevel=None, alwaysSpecifyCompaction=None):
        """
        Generates a PDF417 code (two-dimensional barcode) from input data.

        Attributes: `message` a string, `minWidth` a float, `maxWidth` a float, `minHeight` a float, `maxHeight` a float, `dataColumns` a float, `rows` a float, `preferredAspectRatio` a float, `compactionMode` a float, `compactStyle` a bool, `correctionLevel` a float, `alwaysSpecifyCompaction` a bool.
        """
        attr = dict()
        if message:
            attr["inputMessage"] = AppKit.NSData.dataWithBytes_length_(message, len(message))
        if minWidth:
            attr["inputMinWidth"] = minWidth
        if maxWidth:
            attr["inputMaxWidth"] = maxWidth
        if minHeight:
            attr["inputMinHeight"] = minHeight
        if maxHeight:
            attr["inputMaxHeight"] = maxHeight
        if dataColumns:
            attr["inputDataColumns"] = dataColumns
        if rows:
            attr["inputRows"] = rows
        if preferredAspectRatio:
            attr["inputPreferredAspectRatio"] = preferredAspectRatio
        if compactionMode:
            attr["inputCompactionMode"] = compactionMode
        if compactStyle:
            attr["inputCompactStyle"] = compactStyle
        if correctionLevel:
            attr["inputCorrectionLevel"] = correctionLevel
        if alwaysSpecifyCompaction:
            attr["inputAlwaysSpecifyCompaction"] = alwaysSpecifyCompaction
        filterDict = dict(name="CIPDF417BarcodeGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def randomGenerator(self, size):
        """
        Generates an image of infinite extent whose pixel values are made up of four independent, uniformly-distributed random numbers in the 0 to 1 range.
        """
        attr = dict()
        filterDict = dict(name="CIRandomGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def starShineGenerator(self, size, center=None, color=None, radius=None, crossScale=None, crossAngle=None, crossOpacity=None, crossWidth=None, epsilon=None):
        """
        Generates a starburst pattern that is similar to a supernova; can be used to simulate a lens flare.

        Attributes: `center` a tuple (x, y), `color` RGBA tuple Color (r, g, b, a), `radius` a float, `crossScale` a float, `crossAngle` a float in degrees, `crossOpacity` a float, `crossWidth` a float, `epsilon` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        if radius:
            attr["inputRadius"] = radius
        if crossScale:
            attr["inputCrossScale"] = crossScale
        if crossAngle:
            attr["inputCrossAngle"] = radians(crossAngle)
        if crossOpacity:
            attr["inputCrossOpacity"] = crossOpacity
        if crossWidth:
            attr["inputCrossWidth"] = crossWidth
        if epsilon:
            attr["inputEpsilon"] = epsilon
        filterDict = dict(name="CIStarShineGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def stripesGenerator(self, size, center=None, color0=None, color1=None, width=None, sharpness=None):
        """
        Generates a stripe pattern.

        Attributes: `center` a tuple (x, y), `color0` RGBA tuple Color (r, g, b, a), `color1` RGBA tuple Color (r, g, b, a), `width` a float, `sharpness` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if color0:
            attr["inputColor0"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3])
        if color1:
            attr["inputColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
        if width:
            attr["inputWidth"] = width
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CIStripesGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def sunbeamsGenerator(self, size, center=None, color=None, sunRadius=None, maxStriationRadius=None, striationStrength=None, striationContrast=None, time=None):
        """
        Generates a sun effect.

        Attributes: `center` a tuple (x, y), `color` RGBA tuple Color (r, g, b, a), `sunRadius` a float, `maxStriationRadius` a float, `striationStrength` a float, `striationContrast` a float, `time` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        if sunRadius:
            attr["inputSunRadius"] = sunRadius
        if maxStriationRadius:
            attr["inputMaxStriationRadius"] = maxStriationRadius
        if striationStrength:
            attr["inputStriationStrength"] = striationStrength
        if striationContrast:
            attr["inputStriationContrast"] = striationContrast
        if time:
            attr["inputTime"] = time
        filterDict = dict(name="CISunbeamsGenerator", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def crop(self, rectangle=None):
        """
        Applies a crop to an image.

        Attributes: `rectangle` a tuple (x, y, w, h).
        """
        attr = dict()
        if rectangle:
            attr["inputRectangle"] = AppKit.CIVector.vectorWithValues_count_(rectangle, 4)
        filterDict = dict(name="CICrop", attributes=attr)
        self._addFilter(filterDict)

    def lanczosScaleTransform(self, scale=None, aspectRatio=None):
        """
        Produces a high-quality, scaled version of a source image.

        Attributes: `scale` a float, `aspectRatio` a float.
        """
        attr = dict()
        if scale:
            attr["inputScale"] = scale
        if aspectRatio:
            attr["inputAspectRatio"] = aspectRatio
        filterDict = dict(name="CILanczosScaleTransform", attributes=attr)
        self._addFilter(filterDict)

    def perspectiveCorrection(self, topLeft=None, topRight=None, bottomRight=None, bottomLeft=None):
        """
        Applies a perspective correction, transforming an arbitrary quadrilateral region in the source image to a rectangular output image.

        Attributes: `topLeft` a tuple (x, y), `topRight` a tuple (x, y), `bottomRight` a tuple (x, y), `bottomLeft` a tuple (x, y).
        """
        attr = dict()
        if topLeft:
            attr["inputTopLeft"] = AppKit.CIVector.vectorWithValues_count_(topLeft, 2)
        if topRight:
            attr["inputTopRight"] = AppKit.CIVector.vectorWithValues_count_(topRight, 2)
        if bottomRight:
            attr["inputBottomRight"] = AppKit.CIVector.vectorWithValues_count_(bottomRight, 2)
        if bottomLeft:
            attr["inputBottomLeft"] = AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2)
        filterDict = dict(name="CIPerspectiveCorrection", attributes=attr)
        self._addFilter(filterDict)

    def perspectiveTransform(self, topLeft=None, topRight=None, bottomRight=None, bottomLeft=None):
        """
        Alters the geometry of an image to simulate the observer changing viewing position.

        Attributes: `topLeft` a tuple (x, y), `topRight` a tuple (x, y), `bottomRight` a tuple (x, y), `bottomLeft` a tuple (x, y).
        """
        attr = dict()
        if topLeft:
            attr["inputTopLeft"] = AppKit.CIVector.vectorWithValues_count_(topLeft, 2)
        if topRight:
            attr["inputTopRight"] = AppKit.CIVector.vectorWithValues_count_(topRight, 2)
        if bottomRight:
            attr["inputBottomRight"] = AppKit.CIVector.vectorWithValues_count_(bottomRight, 2)
        if bottomLeft:
            attr["inputBottomLeft"] = AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2)
        filterDict = dict(name="CIPerspectiveTransform", attributes=attr)
        self._addFilter(filterDict)

    def straightenFilter(self, angle=None):
        """
        Rotates the source image by the specified angle in radians.

        Attributes: `angle` a float in degrees.
        """
        attr = dict()
        if angle:
            attr["inputAngle"] = radians(angle)
        filterDict = dict(name="CIStraightenFilter", attributes=attr)
        self._addFilter(filterDict)

    def gaussianGradient(self, size, center=None, color0=None, color1=None, radius=None):
        """
        Generates a gradient that varies from one color to another using a Gaussian distribution.

        Attributes: `center` a tuple (x, y), `color0` RGBA tuple Color (r, g, b, a), `color1` RGBA tuple Color (r, g, b, a), `radius` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if color0:
            attr["inputColor0"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3])
        if color1:
            attr["inputColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIGaussianGradient", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def linearGradient(self, size, point0=None, point1=None, color0=None, color1=None):
        """
        Generates a gradient that varies along a linear axis between two defined endpoints.

        Attributes: `point0` a tuple (x, y), `point1` a tuple (x, y), `color0` RGBA tuple Color (r, g, b, a), `color1` RGBA tuple Color (r, g, b, a).
        """
        attr = dict()
        if point0:
            attr["inputPoint0"] = AppKit.CIVector.vectorWithValues_count_(point0, 2)
        if point1:
            attr["inputPoint1"] = AppKit.CIVector.vectorWithValues_count_(point1, 2)
        if color0:
            attr["inputColor0"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3])
        if color1:
            attr["inputColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
        filterDict = dict(name="CILinearGradient", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def radialGradient(self, size, center=None, radius0=None, radius1=None, color0=None, color1=None):
        """
        Generates a gradient that varies radially between two circles having the same center.

        Attributes: `center` a tuple (x, y), `radius0` a float, `radius1` a float, `color0` RGBA tuple Color (r, g, b, a), `color1` RGBA tuple Color (r, g, b, a).
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if radius0:
            attr["inputRadius0"] = radius0
        if radius1:
            attr["inputRadius1"] = radius1
        if color0:
            attr["inputColor0"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3])
        if color1:
            attr["inputColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
        filterDict = dict(name="CIRadialGradient", attributes=attr)
        filterDict["size"] = size
        filterDict["isGenerator"] = True
        self._addFilter(filterDict)

    def circularScreen(self, center=None, width=None, sharpness=None):
        """
        Simulates a circular-shaped halftone screen.

        Attributes: `center` a tuple (x, y), `width` a float, `sharpness` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if width:
            attr["inputWidth"] = width
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CICircularScreen", attributes=attr)
        self._addFilter(filterDict)

    def CMYKHalftone(self, center=None, width=None, angle=None, sharpness=None, GCR=None, UCR=None):
        """
        Creates a color, halftoned rendition of the source image, using cyan, magenta, yellow, and black inks over a white page.

        Attributes: `center` a tuple (x, y), `width` a float, `angle` a float in degrees, `sharpness` a float, `GCR` a float, `UCR` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if width:
            attr["inputWidth"] = width
        if angle:
            attr["inputAngle"] = radians(angle)
        if sharpness:
            attr["inputSharpness"] = sharpness
        if GCR:
            attr["inputGCR"] = GCR
        if UCR:
            attr["inputUCR"] = UCR
        filterDict = dict(name="CICMYKHalftone", attributes=attr)
        self._addFilter(filterDict)

    def dotScreen(self, center=None, angle=None, width=None, sharpness=None):
        """
        Simulates the dot patterns of a halftone screen.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float, `sharpness` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CIDotScreen", attributes=attr)
        self._addFilter(filterDict)

    def hatchedScreen(self, center=None, angle=None, width=None, sharpness=None):
        """
        Simulates the hatched pattern of a halftone screen.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float, `sharpness` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CIHatchedScreen", attributes=attr)
        self._addFilter(filterDict)

    def lineScreen(self, center=None, angle=None, width=None, sharpness=None):
        """
        Simulates the line pattern of a halftone screen.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float, `sharpness` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CILineScreen", attributes=attr)
        self._addFilter(filterDict)

    def areaAverage(self, extent=None):
        """
        Returns a single-pixel image that contains the average color for the region of interest.

        Attributes: `extent` a tuple (x, y, w, h).
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        filterDict = dict(name="CIAreaAverage", attributes=attr)
        self._addFilter(filterDict)

    def areaHistogram(self, extent=None, count=None, scale=None):
        """
        Returns a 1D image (inputCount wide by one pixel high) that contains the component-wise histogram computed for the specified rectangular area.

        Attributes: `extent` a tuple (x, y, w, h), `count` a float, `scale` a float.
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        if count:
            attr["inputCount"] = count
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIAreaHistogram", attributes=attr)
        self._addFilter(filterDict)

    def rowAverage(self, extent=None):
        """
        Returns a 1-pixel high image that contains the average color for each scan row.

        Attributes: `extent` a tuple (x, y, w, h).
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        filterDict = dict(name="CIRowAverage", attributes=attr)
        self._addFilter(filterDict)

    def columnAverage(self, extent=None):
        """
        Returns a 1-pixel high image that contains the average color for each scan column.

        Attributes: `extent` a tuple (x, y, w, h).
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        filterDict = dict(name="CIColumnAverage", attributes=attr)
        self._addFilter(filterDict)

    def histogramDisplayFilter(self, height=None, highLimit=None, lowLimit=None):
        """
        Generates a histogram image from the output of the `areaHistogram` filter.

        Attributes: `height` a float, `highLimit` a float, `lowLimit` a float.
        """
        attr = dict()
        if height:
            attr["inputHeight"] = height
        if highLimit:
            attr["inputHighLimit"] = highLimit
        if lowLimit:
            attr["inputLowLimit"] = lowLimit
        filterDict = dict(name="CIHistogramDisplayFilter", attributes=attr)
        self._addFilter(filterDict)

    def areaMaximum(self, extent=None):
        """
        Returns a single-pixel image that contains the maximum color components for the region of interest.

        Attributes: `extent` a tuple (x, y, w, h).
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        filterDict = dict(name="CIAreaMaximum", attributes=attr)
        self._addFilter(filterDict)

    def areaMinimum(self, extent=None):
        """
        Returns a single-pixel image that contains the minimum color components for the region of interest.

        Attributes: `extent` a tuple (x, y, w, h).
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        filterDict = dict(name="CIAreaMinimum", attributes=attr)
        self._addFilter(filterDict)

    def areaMaximumAlpha(self, extent=None):
        """
        Returns a single-pixel image that contains the color vector with the maximum alpha value for the region of interest.

        Attributes: `extent` a tuple (x, y, w, h).
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        filterDict = dict(name="CIAreaMaximumAlpha", attributes=attr)
        self._addFilter(filterDict)

    def areaMinimumAlpha(self, extent=None):
        """
        Returns a single-pixel image that contains the color vector with the minimum alpha value for the region of interest.

        Attributes: `extent` a tuple (x, y, w, h).
        """
        attr = dict()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        filterDict = dict(name="CIAreaMinimumAlpha", attributes=attr)
        self._addFilter(filterDict)

    def sharpenLuminance(self, sharpness=None):
        """
        Increases image detail by sharpening.

        Attributes: `sharpness` a float.
        """
        attr = dict()
        if sharpness:
            attr["inputSharpness"] = sharpness
        filterDict = dict(name="CISharpenLuminance", attributes=attr)
        self._addFilter(filterDict)

    def unsharpMask(self, radius=None, intensity=None):
        """
        Increases the contrast of the edges between pixels of different colors in an image.

        Attributes: `radius` a float, `intensity` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        if intensity:
            attr["inputIntensity"] = intensity
        filterDict = dict(name="CIUnsharpMask", attributes=attr)
        self._addFilter(filterDict)

    def blendWithAlphaMask(self, backgroundImage=None, maskImage=None):
        """
        Uses alpha values from a mask to interpolate between an image and the background.

        Attributes: `backgroundImage` an Image object, `maskImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        if maskImage:
            attr["inputMaskImage"] = maskImage._ciImage()
        filterDict = dict(name="CIBlendWithAlphaMask", attributes=attr)
        self._addFilter(filterDict)

    def blendWithMask(self, backgroundImage=None, maskImage=None):
        """
        Uses values from a grayscale mask to interpolate between an image and the background.

        Attributes: `backgroundImage` an Image object, `maskImage` an Image object.
        """
        attr = dict()
        if backgroundImage:
            attr["inputBackgroundImage"] = backgroundImage._ciImage()
        if maskImage:
            attr["inputMaskImage"] = maskImage._ciImage()
        filterDict = dict(name="CIBlendWithMask", attributes=attr)
        self._addFilter(filterDict)

    def bloom(self, radius=None, intensity=None):
        """
        Softens edges and applies a pleasant glow to an image.

        Attributes: `radius` a float, `intensity` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        if intensity:
            attr["inputIntensity"] = intensity
        filterDict = dict(name="CIBloom", attributes=attr)
        self._addFilter(filterDict)

    def comicEffect(self):
        """
        Simulates a comic book drawing by outlining edges and applying a color halftone effect.
        """
        attr = dict()
        filterDict = dict(name="CIComicEffect", attributes=attr)
        self._addFilter(filterDict)

    def convolution3X3(self, weights=None, bias=None):
        """
        Modifies pixel values by performing a 3x3 matrix convolution.

        Attributes: `weights` a float, `bias` a float.
        """
        attr = dict()
        if weights:
            attr["inputWeights"] = weights
        if bias:
            attr["inputBias"] = bias
        filterDict = dict(name="CIConvolution3X3", attributes=attr)
        self._addFilter(filterDict)

    def convolution5X5(self, weights=None, bias=None):
        """
        Modifies pixel values by performing a 5x5 matrix convolution.

        Attributes: `weights` a float, `bias` a float.
        """
        attr = dict()
        if weights:
            attr["inputWeights"] = weights
        if bias:
            attr["inputBias"] = bias
        filterDict = dict(name="CIConvolution5X5", attributes=attr)
        self._addFilter(filterDict)

    def convolution7X7(self, weights=None, bias=None):
        """
        Modifies pixel values by performing a 7x7 matrix convolution.

        Attributes: `weights` a float, `bias` a float.
        """
        attr = dict()
        if weights:
            attr["inputWeights"] = weights
        if bias:
            attr["inputBias"] = bias
        filterDict = dict(name="CIConvolution7X7", attributes=attr)
        self._addFilter(filterDict)

    def convolution9Horizontal(self, weights=None, bias=None):
        """
        Modifies pixel values by performing a 9-element horizontal convolution.

        Attributes: `weights` a float, `bias` a float.
        """
        attr = dict()
        if weights:
            attr["inputWeights"] = weights
        if bias:
            attr["inputBias"] = bias
        filterDict = dict(name="CIConvolution9Horizontal", attributes=attr)
        self._addFilter(filterDict)

    def convolution9Vertical(self, weights=None, bias=None):
        """
        Modifies pixel values by performing a 9-element vertical convolution.

        Attributes: `weights` a float, `bias` a float.
        """
        attr = dict()
        if weights:
            attr["inputWeights"] = weights
        if bias:
            attr["inputBias"] = bias
        filterDict = dict(name="CIConvolution9Vertical", attributes=attr)
        self._addFilter(filterDict)

    def crystallize(self, radius=None, center=None):
        """
        Creates polygon-shaped color blocks by aggregating source pixel-color values.

        Attributes: `radius` a float, `center` a tuple (x, y).
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        filterDict = dict(name="CICrystallize", attributes=attr)
        self._addFilter(filterDict)

    def depthOfField(self, point0=None, point1=None, saturation=None, unsharpMaskRadius=None, unsharpMaskIntensity=None, radius=None):
        """
        Simulates a depth of field effect.

        Attributes: `point0` a tuple (x, y), `point1` a tuple (x, y), `saturation` a float, `unsharpMaskRadius` a float, `unsharpMaskIntensity` a float, `radius` a float.
        """
        attr = dict()
        if point0:
            attr["inputPoint0"] = AppKit.CIVector.vectorWithValues_count_(point0, 2)
        if point1:
            attr["inputPoint1"] = AppKit.CIVector.vectorWithValues_count_(point1, 2)
        if saturation:
            attr["inputSaturation"] = saturation
        if unsharpMaskRadius:
            attr["inputUnsharpMaskRadius"] = unsharpMaskRadius
        if unsharpMaskIntensity:
            attr["inputUnsharpMaskIntensity"] = unsharpMaskIntensity
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIDepthOfField", attributes=attr)
        self._addFilter(filterDict)

    def edges(self, intensity=None):
        """
        Finds all edges in an image and displays them in color.

        Attributes: `intensity` a float.
        """
        attr = dict()
        if intensity:
            attr["inputIntensity"] = intensity
        filterDict = dict(name="CIEdges", attributes=attr)
        self._addFilter(filterDict)

    def edgeWork(self, radius=None):
        """
        Produces a stylized black-and-white rendition of an image that looks similar to a woodblock cutout.

        Attributes: `radius` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIEdgeWork", attributes=attr)
        self._addFilter(filterDict)

    def gloom(self, radius=None, intensity=None):
        """
        Dulls the highlights of an image.

        Attributes: `radius` a float, `intensity` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        if intensity:
            attr["inputIntensity"] = intensity
        filterDict = dict(name="CIGloom", attributes=attr)
        self._addFilter(filterDict)

    def heightFieldFromMask(self, radius=None):
        """
        Produces a continuous three-dimensional, loft-shaped height field from a grayscale mask.

        Attributes: `radius` a float.
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIHeightFieldFromMask", attributes=attr)
        self._addFilter(filterDict)

    def hexagonalPixellate(self, center=None, scale=None):
        """
        Maps an image to colored hexagons whose color is defined by the replaced pixels.

        Attributes: `center` a tuple (x, y), `scale` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIHexagonalPixellate", attributes=attr)
        self._addFilter(filterDict)

    def highlightShadowAdjust(self, highlightAmount=None, shadowAmount=None):
        """
        Adjust the tonal mapping of an image while preserving spatial detail.

        Attributes: `highlightAmount` a float, `shadowAmount` a float.
        """
        attr = dict()
        if highlightAmount:
            attr["inputHighlightAmount"] = highlightAmount
        if shadowAmount:
            attr["inputShadowAmount"] = shadowAmount
        filterDict = dict(name="CIHighlightShadowAdjust", attributes=attr)
        self._addFilter(filterDict)

    def lineOverlay(self, noiseLevel=None, sharpness=None, edgeIntensity=None, threshold=None, contrast=None):
        """
        Creates a sketch that outlines the edges of an image in black.

        Attributes: `noiseLevel` a float, `sharpness` a float, `edgeIntensity` a float, `threshold` a float, `contrast` a float.
        """
        attr = dict()
        if noiseLevel:
            attr["inputNRNoiseLevel"] = noiseLevel
        if sharpness:
            attr["inputNRSharpness"] = sharpness
        if edgeIntensity:
            attr["inputEdgeIntensity"] = edgeIntensity
        if threshold:
            attr["inputThreshold"] = threshold
        if contrast:
            attr["inputContrast"] = contrast
        filterDict = dict(name="CILineOverlay", attributes=attr)
        self._addFilter(filterDict)

    def pixellate(self, center=None, scale=None):
        """
        Makes an image blocky by mapping the image to colored squares whose color is defined by the replaced pixels.

        Attributes: `center` a tuple (x, y), `scale` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIPixellate", attributes=attr)
        self._addFilter(filterDict)

    def pointillize(self, radius=None, center=None):
        """
        Renders the source image in a pointillistic style.

        Attributes: `radius` a float, `center` a tuple (x, y).
        """
        attr = dict()
        if radius:
            attr["inputRadius"] = radius
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        filterDict = dict(name="CIPointillize", attributes=attr)
        self._addFilter(filterDict)

    def shadedMaterial(self, shadingImage=None, scale=None):
        """
        Produces a shaded image from a height field.

        Attributes: `shadingImage` an Image object, `scale` a float.
        """
        attr = dict()
        if shadingImage:
            attr["inputShadingImage"] = shadingImage._ciImage()
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIShadedMaterial", attributes=attr)
        self._addFilter(filterDict)

    def spotColor(self, centerColor1=None, replacementColor1=None, closeness1=None, contrast1=None, centerColor2=None, replacementColor2=None, closeness2=None, contrast2=None, centerColor3=None, replacementColor3=None, closeness3=None, contrast3=None):
        """
        Replaces one or more color ranges with spot colors.

        Attributes: `centerColor1` RGBA tuple Color (r, g, b, a), `replacementColor1` RGBA tuple Color (r, g, b, a), `closeness1` a float, `contrast1` a float, `centerColor2` RGBA tuple Color (r, g, b, a), `replacementColor2` RGBA tuple Color (r, g, b, a), `closeness2` a float, `contrast2` a float, `centerColor3` RGBA tuple Color (r, g, b, a), `replacementColor3` RGBA tuple Color (r, g, b, a), `closeness3` a float, `contrast3` a float.
        """
        attr = dict()
        if centerColor1:
            attr["inputCenterColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(centerColor1[0], centerColor1[1], centerColor1[2], centerColor1[3])
        if replacementColor1:
            attr["inputReplacementColor1"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(replacementColor1[0], replacementColor1[1], replacementColor1[2], replacementColor1[3])
        if closeness1:
            attr["inputCloseness1"] = closeness1
        if contrast1:
            attr["inputContrast1"] = contrast1
        if centerColor2:
            attr["inputCenterColor2"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(centerColor2[0], centerColor2[1], centerColor2[2], centerColor2[3])
        if replacementColor2:
            attr["inputReplacementColor2"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(replacementColor2[0], replacementColor2[1], replacementColor2[2], replacementColor2[3])
        if closeness2:
            attr["inputCloseness2"] = closeness2
        if contrast2:
            attr["inputContrast2"] = contrast2
        if centerColor3:
            attr["inputCenterColor3"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(centerColor3[0], centerColor3[1], centerColor3[2], centerColor3[3])
        if replacementColor3:
            attr["inputReplacementColor3"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(replacementColor3[0], replacementColor3[1], replacementColor3[2], replacementColor3[3])
        if closeness3:
            attr["inputCloseness3"] = closeness3
        if contrast3:
            attr["inputContrast3"] = contrast3
        filterDict = dict(name="CISpotColor", attributes=attr)
        self._addFilter(filterDict)

    def spotLight(self, lightPosition=None, lightPointsAt=None, brightness=None, concentration=None, color=None):
        """
        Applies a directional spotlight effect to an image.

        Attributes: `lightPosition` a tulple (x, y, z), `lightPointsAt` a tuple (x, y), `brightness` a float, `concentration` a float, `color` RGBA tuple Color (r, g, b, a).
        """
        attr = dict()
        if lightPosition:
            attr["inputLightPosition"] = AppKit.CIVector.vectorWithValues_count_(lightPosition, 3)
        if lightPointsAt:
            attr["inputLightPointsAt"] = AppKit.CIVector.vectorWithValues_count_(lightPointsAt, 2)
        if brightness:
            attr["inputBrightness"] = brightness
        if concentration:
            attr["inputConcentration"] = concentration
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        filterDict = dict(name="CISpotLight", attributes=attr)
        self._addFilter(filterDict)

    def affineClamp(self, transform=None):
        """
        Performs an affine transform on a source image and then clamps the pixels at the edge of the transformed image, extending them outwards.

        Attributes: `transform`.
        """
        attr = dict()
        if transform:
            attr["inputTransform"] = transform
        filterDict = dict(name="CIAffineClamp", attributes=attr)
        self._addFilter(filterDict)

    def affineTile(self, transform=None):
        """
        Applies an affine transform to an image and then tiles the transformed image.

        Attributes: `transform`.
        """
        attr = dict()
        if transform:
            attr["inputTransform"] = transform
        filterDict = dict(name="CIAffineTile", attributes=attr)
        self._addFilter(filterDict)

    def eightfoldReflectedTile(self, center=None, angle=None, width=None):
        """
        Produces a tiled image from a source image by applying an 8-way reflected symmetry.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CIEightfoldReflectedTile", attributes=attr)
        self._addFilter(filterDict)

    def fourfoldReflectedTile(self, center=None, angle=None, acuteAngle=None, width=None):
        """
        Produces a tiled image from a source image by applying a 4-way reflected symmetry.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `acuteAngle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if acuteAngle:
            attr["inputAcuteAngle"] = radians(acuteAngle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CIFourfoldReflectedTile", attributes=attr)
        self._addFilter(filterDict)

    def fourfoldRotatedTile(self, center=None, angle=None, width=None):
        """
        Produces a tiled image from a source image by rotating the source image at increments of 90 degrees.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CIFourfoldRotatedTile", attributes=attr)
        self._addFilter(filterDict)

    def fourfoldTranslatedTile(self, center=None, angle=None, acuteAngle=None, width=None):
        """
        Produces a tiled image from a source image by applying 4 translation operations.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `acuteAngle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if acuteAngle:
            attr["inputAcuteAngle"] = radians(acuteAngle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CIFourfoldTranslatedTile", attributes=attr)
        self._addFilter(filterDict)

    def glideReflectedTile(self, center=None, angle=None, width=None):
        """
        Produces a tiled image from a source image by translating and smearing the image.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CIGlideReflectedTile", attributes=attr)
        self._addFilter(filterDict)

    def kaleidoscope(self, count=None, center=None, angle=None):
        """
        Produces a kaleidoscopic image from a source image by applying 12-way symmetry.

        Attributes: `count` a float, `center` a tuple (x, y), `angle` a float in degrees.
        """
        attr = dict()
        if count:
            attr["inputCount"] = count
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        filterDict = dict(name="CIKaleidoscope", attributes=attr)
        self._addFilter(filterDict)

    def opTile(self, center=None, scale=None, angle=None, width=None):
        """
        Segments an image, applying any specified scaling and rotation, and then assembles the image again to give an op art appearance.

        Attributes: `center` a tuple (x, y), `scale` a float, `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if scale:
            attr["inputScale"] = scale
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CIOpTile", attributes=attr)
        self._addFilter(filterDict)

    def parallelogramTile(self, center=None, angle=None, acuteAngle=None, width=None):
        """
        Warps an image by reflecting it in a parallelogram, and then tiles the result.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `acuteAngle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if acuteAngle:
            attr["inputAcuteAngle"] = radians(acuteAngle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CIParallelogramTile", attributes=attr)
        self._addFilter(filterDict)

    def perspectiveTile(self, topLeft=None, topRight=None, bottomRight=None, bottomLeft=None):
        """
        Applies a perspective transform to an image and then tiles the result.

        Attributes: `topLeft` a tuple (x, y), `topRight` a tuple (x, y), `bottomRight` a tuple (x, y), `bottomLeft` a tuple (x, y).
        """
        attr = dict()
        if topLeft:
            attr["inputTopLeft"] = AppKit.CIVector.vectorWithValues_count_(topLeft, 2)
        if topRight:
            attr["inputTopRight"] = AppKit.CIVector.vectorWithValues_count_(topRight, 2)
        if bottomRight:
            attr["inputBottomRight"] = AppKit.CIVector.vectorWithValues_count_(bottomRight, 2)
        if bottomLeft:
            attr["inputBottomLeft"] = AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2)
        filterDict = dict(name="CIPerspectiveTile", attributes=attr)
        self._addFilter(filterDict)

    def sixfoldReflectedTile(self, center=None, angle=None, width=None):
        """
        Produces a tiled image from a source image by applying a 6-way reflected symmetry.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CISixfoldReflectedTile", attributes=attr)
        self._addFilter(filterDict)

    def sixfoldRotatedTile(self, center=None, angle=None, width=None):
        """
        Produces a tiled image from a source image by rotating the source image at increments of 60 degrees.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CISixfoldRotatedTile", attributes=attr)
        self._addFilter(filterDict)

    def triangleTile(self, center=None, angle=None, width=None):
        """
        Maps a triangular portion of image to a triangular area and then tiles the result.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CITriangleTile", attributes=attr)
        self._addFilter(filterDict)

    def twelvefoldReflectedTile(self, center=None, angle=None, width=None):
        """
        Produces a tiled image from a source image by rotating the source image at increments of 30 degrees.

        Attributes: `center` a tuple (x, y), `angle` a float in degrees, `width` a float.
        """
        attr = dict()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        filterDict = dict(name="CITwelvefoldReflectedTile", attributes=attr)
        self._addFilter(filterDict)

    def accordionFoldTransition(self, targetImage=None, bottomHeight=None, numberOfFolds=None, foldShadowAmount=None, time=None):
        """
        Transitions from one image to another of differing dimensions by unfolding and crossfading.

        Attributes: `targetImage` an Image object, `bottomHeight` a float, `numberOfFolds` a float, `foldShadowAmount` a float, `time` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if bottomHeight:
            attr["inputBottomHeight"] = bottomHeight
        if numberOfFolds:
            attr["inputNumberOfFolds"] = numberOfFolds
        if foldShadowAmount:
            attr["inputFoldShadowAmount"] = foldShadowAmount
        if time:
            attr["inputTime"] = time
        filterDict = dict(name="CIAccordionFoldTransition", attributes=attr)
        self._addFilter(filterDict)

    def barsSwipeTransition(self, targetImage=None, angle=None, width=None, barOffset=None, time=None):
        """
        Transitions from one image to another by passing a bar over the source image.

        Attributes: `targetImage` an Image object, `angle` a float in degrees, `width` a float, `barOffset` a float, `time` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        if barOffset:
            attr["inputBarOffset"] = barOffset
        if time:
            attr["inputTime"] = time
        filterDict = dict(name="CIBarsSwipeTransition", attributes=attr)
        self._addFilter(filterDict)

    def copyMachineTransition(self, targetImage=None, extent=None, color=None, time=None, angle=None, width=None, opacity=None):
        """
        Transitions from one image to another by simulating the effect of a copy machine.

        Attributes: `targetImage` an Image object, `extent` a tuple (x, y, w, h), `color` RGBA tuple Color (r, g, b, a), `time` a float, `angle` a float in degrees, `width` a float, `opacity` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        if time:
            attr["inputTime"] = time
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        if opacity:
            attr["inputOpacity"] = opacity
        filterDict = dict(name="CICopyMachineTransition", attributes=attr)
        self._addFilter(filterDict)

    def disintegrateWithMaskTransition(self, targetImage=None, maskImage=None, time=None, shadowRadius=None, shadowDensity=None, shadowOffset=None):
        """
        Transitions from one image to another using the shape defined by a mask.

        Attributes: `targetImage` an Image object, `maskImage` an Image object, `time` a float, `shadowRadius` a float, `shadowDensity` a float, `shadowOffset` a tuple (x, y).
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if maskImage:
            attr["inputMaskImage"] = maskImage._ciImage()
        if time:
            attr["inputTime"] = time
        if shadowRadius:
            attr["inputShadowRadius"] = shadowRadius
        if shadowDensity:
            attr["inputShadowDensity"] = shadowDensity
        if shadowOffset:
            attr["inputShadowOffset"] = AppKit.CIVector.vectorWithValues_count_(shadowOffset, 2)
        filterDict = dict(name="CIDisintegrateWithMaskTransition", attributes=attr)
        self._addFilter(filterDict)

    def dissolveTransition(self, targetImage=None, time=None):
        """
        Uses a dissolve to transition from one image to another.

        Attributes: `targetImage` an Image object, `time` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if time:
            attr["inputTime"] = time
        filterDict = dict(name="CIDissolveTransition", attributes=attr)
        self._addFilter(filterDict)

    def flashTransition(self, targetImage=None, center=None, extent=None, color=None, time=None, maxStriationRadius=None, striationStrength=None, striationContrast=None, fadeThreshold=None):
        """
        Transitions from one image to another by creating a flash.

        Attributes: `targetImage` an Image object, `center` a tuple (x, y), `extent` a tuple (x, y, w, h), `color` RGBA tuple Color (r, g, b, a), `time` a float, `maxStriationRadius` a float, `striationStrength` a float, `striationContrast` a float, `fadeThreshold` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        if time:
            attr["inputTime"] = time
        if maxStriationRadius:
            attr["inputMaxStriationRadius"] = maxStriationRadius
        if striationStrength:
            attr["inputStriationStrength"] = striationStrength
        if striationContrast:
            attr["inputStriationContrast"] = striationContrast
        if fadeThreshold:
            attr["inputFadeThreshold"] = fadeThreshold
        filterDict = dict(name="CIFlashTransition", attributes=attr)
        self._addFilter(filterDict)

    def modTransition(self, targetImage=None, center=None, time=None, angle=None, radius=None, compression=None):
        """
        Transitions from one image to another by revealing the target image through irregularly shaped holes.

        Attributes: `targetImage` an Image object, `center` a tuple (x, y), `time` a float, `angle` a float in degrees, `radius` a float, `compression` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if time:
            attr["inputTime"] = time
        if angle:
            attr["inputAngle"] = radians(angle)
        if radius:
            attr["inputRadius"] = radius
        if compression:
            attr["inputCompression"] = compression
        filterDict = dict(name="CIModTransition", attributes=attr)
        self._addFilter(filterDict)

    def pageCurlTransition(self, targetImage=None, backsideImage=None, shadingImage=None, extent=None, time=None, angle=None, radius=None):
        """
        Transitions from one image to another by simulating a curling page, revealing the new image as the page curls.

        Attributes: `targetImage` an Image object, `backsideImage` an Image object, `shadingImage` an Image object, `extent` a tuple (x, y, w, h), `time` a float, `angle` a float in degrees, `radius` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if backsideImage:
            attr["inputBacksideImage"] = backsideImage._ciImage()
        if shadingImage:
            attr["inputShadingImage"] = shadingImage._ciImage()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        if time:
            attr["inputTime"] = time
        if angle:
            attr["inputAngle"] = radians(angle)
        if radius:
            attr["inputRadius"] = radius
        filterDict = dict(name="CIPageCurlTransition", attributes=attr)
        self._addFilter(filterDict)

    def pageCurlWithShadowTransition(self, targetImage=None, backsideImage=None, extent=None, time=None, angle=None, radius=None, shadowSize=None, shadowAmount=None, shadowExtent=None):
        """
        Transitions from one image to another by simulating a curling page, revealing the new image as the page curls.

        Attributes: `targetImage` an Image object, `backsideImage` an Image object, `extent` a tuple (x, y, w, h), `time` a float, `angle` a float in degrees, `radius` a float, `shadowSize` a float, `shadowAmount` a float, `shadowExtent` a tuple (x, y, w, h).
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if backsideImage:
            attr["inputBacksideImage"] = backsideImage._ciImage()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        if time:
            attr["inputTime"] = time
        if angle:
            attr["inputAngle"] = radians(angle)
        if radius:
            attr["inputRadius"] = radius
        if shadowSize:
            attr["inputShadowSize"] = shadowSize
        if shadowAmount:
            attr["inputShadowAmount"] = shadowAmount
        if shadowExtent:
            attr["inputShadowExtent"] = AppKit.CIVector.vectorWithValues_count_(shadowExtent, 4)
        filterDict = dict(name="CIPageCurlWithShadowTransition", attributes=attr)
        self._addFilter(filterDict)

    def rippleTransition(self, targetImage=None, shadingImage=None, center=None, extent=None, time=None, width=None, scale=None):
        """
        Transitions from one image to another by creating a circular wave that expands from the center point, revealing the new image in the wake of the wave.

        Attributes: `targetImage` an Image object, `shadingImage` an Image object, `center` a tuple (x, y), `extent` a tuple (x, y, w, h), `time` a float, `width` a float, `scale` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if shadingImage:
            attr["inputShadingImage"] = shadingImage._ciImage()
        if center:
            attr["inputCenter"] = AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        if time:
            attr["inputTime"] = time
        if width:
            attr["inputWidth"] = width
        if scale:
            attr["inputScale"] = scale
        filterDict = dict(name="CIRippleTransition", attributes=attr)
        self._addFilter(filterDict)

    def swipeTransition(self, targetImage=None, extent=None, color=None, time=None, angle=None, width=None, opacity=None):
        """
        Transitions from one image to another by simulating a swiping action.

        Attributes: `targetImage` an Image object, `extent` a tuple (x, y, w, h), `color` RGBA tuple Color (r, g, b, a), `time` a float, `angle` a float in degrees, `width` a float, `opacity` a float.
        """
        attr = dict()
        if targetImage:
            attr["inputTargetImage"] = targetImage._ciImage()
        if extent:
            attr["inputExtent"] = AppKit.CIVector.vectorWithValues_count_(extent, 4)
        if color:
            attr["inputColor"] = AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
        if time:
            attr["inputTime"] = time
        if angle:
            attr["inputAngle"] = radians(angle)
        if width:
            attr["inputWidth"] = width
        if opacity:
            attr["inputOpacity"] = opacity
        filterDict = dict(name="CISwipeTransition", attributes=attr)
        self._addFilter(filterDict)
