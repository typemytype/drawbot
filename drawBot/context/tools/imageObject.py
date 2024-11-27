import AppKit # type: ignore
import Quartz # type: ignore
from math import radians
import os
from math import radians
from typing import Any

import AppKit
from typing import Self

from drawBot.aliases import (BoundingBox, Point, RGBAColorTuple, Size, SomePath,
                             TransformTuple)
from drawBot.context.baseContext import FormattedString
from drawBot.context.imageContext import _makeBitmapImageRep
from drawBot.misc import DrawBotError, optimizePath


class ImageObject:

    """
    Return a Image object, packed with filters.
    This is a reusable object. Supports pdf, jpg, png, tiff and gif file formats. `NSImage` objects are supported too.

    .. downloadcode:: imageObject.py

        size(550, 300)
        # initiate a new image object
        im = ImageObject()

        # draw in the image
        # the 'with' statement will create a custom context
        # only drawing in the image object
        with im:
            # set a size for the image
            size(200, 200)
            # draw something
            fill(1, 0, 0)
            rect(0, 0, width(), height())
            fill(1)
            fontSize(30)
            text("Hello World", (10, 10))

        # draw in the image in the main context
        image(im, (10, 50))
        # apply some filters
        im.gaussianBlur()

        # get the offset (with a blur this will be negative)
        x, y = im.offset()
        # draw in the image in the main context
        image(im, (300+x, 50+y))

    """

    # For more info see: `Core Image Filter Reference`_.
    # .. _Core Image Filter Reference: https://developer.apple.com/library/mac/documentation/GraphicsImaging/Reference/CoreImageFilterReference/index.html

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

    def size(self) -> Size:
        """
        Return the size of the image as a tuple.
        """
        (x, y), (w, h) = self._ciImage().extent()
        return w, h

    def offset(self) -> Point:
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

    def open(self, path: SomePath):
        """
        Open an image with a given `path`.
        """
        if isinstance(path, AppKit.NSImage):
            im = path
        elif isinstance(path, (str, os.PathLike)):
            path = optimizePath(path)
            if isinstance(path, str) and path.startswith("http"):
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

    def copy(self) -> Self:
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
        from drawBot.drawBotDrawingTools import (DrawBotDrawingTool,
                                                 _drawBotDrawingTool)

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
        page = data.pageAtIndex_(pageCount - 1)
        # create an image
        im = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation())
        # create an CIImage object
        rep = _makeBitmapImageRep(im)
        ciImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep)
        # merge it with the already set data, if there already an image
        self._merge(ciImage)

    def __enter__(self) -> Self:
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
        Add a filter.
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
        sourceSize = self.size()
        for filterDict in self._filters:
            filterName = filterDict.get("name")
            ciFilter = AppKit.CIFilter.filterWithName_(filterName)
            ciFilter.setDefaults()

            for key, value in filterDict.get("attributes", {}).items():
                ciFilter.setValue_forKey_(value, key)

            if filterDict.get("isGenerator", False):
                generator = ciFilter.valueForKey_("outputImage")
                extent = generator.extent()
                w, h = filterDict.get("size", extent.size)
                dummy = AppKit.NSImage.alloc().initWithSize_((w, h))

                scaleX = w / extent.size.width
                scaleY = h / extent.size.height
                dummy.lockFocus()
                ctx = AppKit.NSGraphicsContext.currentContext()
                ctx.setShouldAntialias_(False)
                ctx.setImageInterpolation_(AppKit.NSImageInterpolationNone)
                fromRect = (0, 0), (w, h)
                if filterDict.get("fitImage", False):
                    transform = AppKit.NSAffineTransform.transform()
                    transform.scaleXBy_yBy_(scaleX, scaleY)
                    transform.concat()
                    fromRect = extent
                generator.drawAtPoint_fromRect_operation_fraction_((0, 0), fromRect, AppKit.NSCompositeCopy, 1)
                dummy.unlockFocus()
                rep = _makeBitmapImageRep(dummy)
                self._cachedImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep)
                del dummy
            elif hasattr(self, "_cachedImage"):
                ciFilter.setValue_forKey_(self._cachedImage, "inputImage")
                self._cachedImage = ciFilter.valueForKey_("outputImage")

        if not hasattr(self, "_cachedImage"):
            raise DrawBotError("Image does not contain any data. Draw into the image object first or set image data from a path.")
        elif Quartz.CGRectIsInfinite(self._cachedImage.extent()):
            # an infinite image
            w, h = self.size()
            dummy = AppKit.NSImage.alloc().initWithSize_(sourceSize)
            dummy.lockFocus()
            self._cachedImage.drawAtPoint_fromRect_operation_fraction_((0, 0), ((0, 0), sourceSize), AppKit.NSCompositeCopy, 1)
            dummy.unlockFocus()
            rep = _makeBitmapImageRep(dummy)
            self._cachedImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep)
            self._cachedImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep)
            del dummy

    # --- filters ---
    def accordionFoldTransition(self, targetImage: Self, bottomHeight: float = 0.0, numberOfFolds: float = 3.0, foldShadowAmount: float = 0.1, time: float = 0.0):
        """
        Transitions from one image to another of a differing dimensions by unfolding.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `bottomHeight` a float. The height in pixels from the bottom of the image to the bottom of the folded part of the transition.
        `numberOfFolds` a float. The number of folds used in the transition.
        `foldShadowAmount` a float. A value that specifies the intensity of the shadow in the transition.
        `time` a float. The duration of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAccordionFoldTransition',
            attributes=dict(
                targetImage=targetImage,
                bottomHeight=bottomHeight,
                numberOfFolds=numberOfFolds,
                foldShadowAmount=foldShadowAmount,
                time=time
            )
        )
        self._addFilter(filterDict)
    
    def additionCompositing(self, backgroundImage: Self):
        """
        Adds color components to achieve a brightening effect. This filter is typically used to add highlights and lens flare effects.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAdditionCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def affineClamp(self, transform: TransformTuple = (0.4, 0.0, 0.0, 0.4, 0.0, 0.0)):
        """
        Performs an affine transformation on a source image and then clamps the pixels at the edge of the transformed image, extending them outwards. This filter performs similarly to the "Affine Transform" filter except that it produces an image with infinite extent. You can use this filter when you need to blur an image but you want to avoid a soft, black fringe along the edges.
        
        **Arguments:**
        
        `transform` a tuple (xx, xy, yx, yy, x, y). The transform to apply to the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAffineClamp',
            attributes=dict(
                transform=transform
            )
        )
        self._addFilter(filterDict)
    
    def affineTile(self, transform: TransformTuple = (0.4, 0.0, 0.0, 0.4, 0.0, 0.0)):
        """
        Applies an affine transformation to an image and then tiles the transformed image.
        
        **Arguments:**
        
        `transform` a tuple (xx, xy, yx, yy, x, y). The transform to apply to the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAffineTile',
            attributes=dict(
                transform=transform
            )
        )
        self._addFilter(filterDict)
    
    def areaAverage(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Calculates the average color for the specified area in an image, returning the result in a pixel.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaAverage',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def areaHistogram(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0), scale: float = 1.0, count: float = 64.0):
        """
        Calculates histograms of the R, G, B, and A channels of the specified area of an image. The output image is a one pixel tall image containing the histogram data for all four channels.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that, after intersection with the image extent, specifies the subregion of the image that you want to process.
        `scale` a float. The scale value to use for the histogram values. If the scale is 1.0, then the bins in the resulting image will add up to 1.0.
        `count` a float. The number of bins for the histogram. This value will determine the width of the output image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaHistogram',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                scale=scale,
                count=count
            )
        )
        self._addFilter(filterDict)
    
    def areaLogarithmicHistogram(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0), scale: float = 1.0, count: float = 64.0, minimumStop: float = -10.0, maximumStop: float = 4.0):
        """
        Calculates histogram of the R, G, B, and A channels of the specified area of an image. Before binning, the R, G, and B channel values are transformed by the log base two function. The output image is a one pixel tall image containing the histogram data for all four channels.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `scale` a float. The amount of the effect.
        `count` a float. The number of bins for the histogram. This value will determine the width of the output image.
        `minimumStop` a float. The minimum of the range of color channel values to be in the logarithmic histogram image.
        `maximumStop` a float. The maximum of the range of color channel values to be in the logarithmic histogram image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaLogarithmicHistogram',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                scale=scale,
                count=count,
                minimumStop=minimumStop,
                maximumStop=maximumStop
            )
        )
        self._addFilter(filterDict)
    
    def areaMaximum(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Calculates the maximum component values for the specified area in an image, returning the result in a pixel.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaMaximum',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def areaMaximumAlpha(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Finds and returns the pixel with the maximum alpha value.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaMaximumAlpha',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def areaMinimum(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Calculates the minimum component values for the specified area in an image, returning the result in a pixel.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaMinimum',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def areaMinimumAlpha(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Finds and returns the pixel with the minimum alpha value.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaMinimumAlpha',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def areaMinMax(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Calculates the per-component minimum and maximum value for the specified area in an image. The result is returned in a 2x1 image where the component minimum values are stored in the pixel on the left.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaMinMax',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def areaMinMaxRed(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Calculates the minimum and maximum red component value for the specified area in an image. The result is returned in the red and green channels of a one pixel image.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAreaMinMaxRed',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def attributedTextImageGenerator(self, size: Size, text: FormattedString, scaleFactor: float = 1.0, padding: float = 0.0):
        """
        Generate an image attributed string.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `text` a `FormattedString`. The attributed text to render.
        `scaleFactor` a float. The scale of the font to use for the generated text.
        `padding` a float. A value for an additional number of pixels to pad around the text’s bounding box.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAttributedTextImageGenerator',
            attributes=dict(
                text=text.getNSObject(),
                scaleFactor=scaleFactor,
                padding=padding
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def aztecCodeGenerator(self, size: Size, message: str, layers, compactStyle, correctionLevel: float = 23.0):
        """
        Generate an Aztec barcode image for message data.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `message` a string. The message to encode in the Aztec Barcode
        `layers` a float. Aztec layers value between 1 and 32. Set to `None` for automatic.
        `compactStyle` a bool. Force a compact style Aztec code to `True` or `False`. Set to `None` for automatic.
        `correctionLevel` a float. Aztec error correction value between 5 and 95
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIAztecCodeGenerator',
            attributes=dict(
                message=AppKit.NSData.dataWithBytes_length_(message, len(message)),
                layers=layers,
                compactStyle=compactStyle,
                correctionLevel=correctionLevel
            ),
            size=size,
            isGenerator=True,
            fitImage=True
        ),
        self._addFilter(filterDict)
    
    def barsSwipeTransition(self, targetImage: Self, angle: float = 3.141592653589793, width: float = 30.0, barOffset: float = 10.0, time: float = 0.0):
        """
        Transitions from one image to another by swiping rectangular portions of the foreground image to disclose the target image.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `angle` a float in degrees. The angle in degrees of the bars.
        `width` a float. The width of each bar.
        `barOffset` a float. The offset of one bar with respect to another.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBarsSwipeTransition',
            attributes=dict(
                targetImage=targetImage,
                angle=radians(angle),
                width=width,
                barOffset=barOffset,
                time=time
            )
        )
        self._addFilter(filterDict)
    
    def blendWithAlphaMask(self, backgroundImage: Self, maskImage: Self):
        """
        Uses values from a mask image to interpolate between an image and the background. When a mask alpha value is 0.0, the result is the background. When the mask alpha value is 1.0, the result is the image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        `maskImage` an Image object. A masking image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBlendWithAlphaMask',
            attributes=dict(
                backgroundImage=backgroundImage,
                maskImage=maskImage
            )
        )
        self._addFilter(filterDict)
    
    def blendWithBlueMask(self, backgroundImage: Self, maskImage: Self):
        """
        Uses values from a mask image to interpolate between an image and the background. When a mask blue value is 0.0, the result is the background. When the mask blue value is 1.0, the result is the image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        `maskImage` an Image object. A masking image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBlendWithBlueMask',
            attributes=dict(
                backgroundImage=backgroundImage,
                maskImage=maskImage
            )
        )
        self._addFilter(filterDict)
    
    def blendWithMask(self, backgroundImage: Self, maskImage: Self):
        """
        Uses values from a grayscale mask to interpolate between an image and the background. When a mask green value is 0.0, the result is the background. When the mask green value is 1.0, the result is the image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        `maskImage` an Image object. A grayscale mask. When a mask value is 0.0, the result is the background. When the mask value is 1.0, the result is the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBlendWithMask',
            attributes=dict(
                backgroundImage=backgroundImage,
                maskImage=maskImage
            )
        )
        self._addFilter(filterDict)
    
    def blendWithRedMask(self, backgroundImage: Self, maskImage: Self):
        """
        Uses values from a mask image to interpolate between an image and the background. When a mask red value is 0.0, the result is the background. When the mask red value is 1.0, the result is the image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        `maskImage` an Image object. A masking image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBlendWithRedMask',
            attributes=dict(
                backgroundImage=backgroundImage,
                maskImage=maskImage
            )
        )
        self._addFilter(filterDict)
    
    def bloom(self, radius: float = 10.0, intensity: float = 0.5):
        """
        Softens edges and applies a pleasant glow to an image.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the effect. The larger the radius, the greater the effect.
        `intensity` a float. The intensity of the effect. A value of 0.0 is no effect. A value of 1.0 is the maximum effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBloom',
            attributes=dict(
                radius=radius,
                intensity=intensity
            )
        )
        self._addFilter(filterDict)
    
    def blurredRectangleGenerator(self, size: Size, extent: BoundingBox = (0.0, 0.0, 100.0, 100.0), sigma: float = 10.0, color: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0)):
        """
        Generates a blurred rectangle image with the specified extent, blur sigma, and color.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `sigma` a float. The sigma for a gaussian blur.
        `color` RGBA tuple Color (r, g, b, a). A color.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBlurredRectangleGenerator',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                sigma=sigma,
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def bokehBlur(self, radius: float = 20.0, ringAmount: float = 0.0, ringSize: float = 0.1, softness: float = 1.0):
        """
        Smooths an image using a disc-shaped convolution kernel.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the blur. The larger the radius, the blurrier the result.
        `ringAmount` a float. The amount of extra emphasis at the ring of the bokeh.
        `ringSize` a float. The size of extra emphasis at the ring of the bokeh.
        `softness` a float. 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBokehBlur',
            attributes=dict(
                radius=radius,
                ringAmount=ringAmount,
                ringSize=ringSize,
                softness=softness
            )
        )
        self._addFilter(filterDict)
    
    def boxBlur(self, radius: float = 10.0):
        """
        Smooths or sharpens an image using a box-shaped convolution kernel.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the blur. The larger the radius, the blurrier the result.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBoxBlur',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def bumpDistortion(self, center: Point = (150.0, 150.0), radius: float = 300.0, scale: float = 0.5):
        """
        Creates a concave or convex bump that originates at a specified point in the image.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        `scale` a float. The scale of the effect determines the curvature of the bump. A value of 0.0 has no effect. Positive values create an outward bump; negative values create an inward bump.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBumpDistortion',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius,
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def bumpDistortionLinear(self, center: Point = (150.0, 150.0), radius: float = 300.0, angle: float = 0.0, scale: float = 0.5):
        """
        Creates a bump that originates from a linear portion of the image.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        `angle` a float in degrees. The angle in degrees of the line around which the distortion occurs.
        `scale` a float. The scale of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIBumpDistortionLinear',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius,
                angle=radians(angle),
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def cannyEdgeDetector(self, gaussianSigma: float = 1.6, perceptual: bool = False, thresholdHigh: float = 0.05, thresholdLow: float = 0.02, hysteresisPasses: float = 1.0):
        """
        Applies the Canny Edge Detection algorithm to an image.
        
        **Arguments:**
        
        `gaussianSigma` a float. The gaussian sigma of blur to apply to the image to reduce high-frequency noise.
        `perceptual` a float. Specifies whether the edge thresholds should be computed in a perceptual color space.
        `thresholdHigh` a float. The threshold that determines if gradient magnitude is a strong edge.
        `thresholdLow` a float. The threshold that determines if gradient magnitude is a weak edge.
        `hysteresisPasses` a float. The number of hysteresis passes to apply to promote weak edge pixels.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICannyEdgeDetector',
            attributes=dict(
                gaussianSigma=gaussianSigma,
                perceptual=perceptual,
                thresholdHigh=thresholdHigh,
                thresholdLow=thresholdLow,
                hysteresisPasses=hysteresisPasses
            )
        )
        self._addFilter(filterDict)
    
    def checkerboardGenerator(self, size: Size, center: Point = (150.0, 150.0), color0: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), color1: RGBAColorTuple = (0.0, 0.0, 0.0, 1.0), width: float = 80.0, sharpness: float = 1.0):
        """
        Generates a pattern of squares of alternating colors. You can specify the size, colors, and the sharpness of the pattern.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `color0` RGBA tuple Color (r, g, b, a). A color to use for the first set of squares.
        `color1` RGBA tuple Color (r, g, b, a). A color to use for the second set of squares.
        `width` a float. The width of the squares in the pattern.
        `sharpness` a float. The sharpness of the edges in pattern. The smaller the value, the more blurry the pattern. Values range from 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICheckerboardGenerator',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                color0=AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3]),
                color1=AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3]),
                width=width,
                sharpness=sharpness
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def circleSplashDistortion(self, center: Point = (150.0, 150.0), radius: float = 150.0):
        """
        Distorts the pixels starting at the circumference of a circle and emanating outward.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICircleSplashDistortion',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def circularScreen(self, center: Point = (150.0, 150.0), width: float = 6.0, sharpness: float = 0.7):
        """
        Simulates a circular-shaped halftone screen.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `width` a float. The distance between each circle in the pattern.
        `sharpness` a float. The sharpness of the circles. The larger the value, the sharper the circles.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICircularScreen',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                width=width,
                sharpness=sharpness
            )
        )
        self._addFilter(filterDict)
    
    def circularWrap(self, center: Point = (150.0, 150.0), radius: float = 150.0, angle: float = 0.0):
        """
        Wraps an image around a transparent circle. The distortion of the image increases with the distance from the center of the circle.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        `angle` a float in degrees. The angle in degrees of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICircularWrap',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius,
                angle=radians(angle)
            )
        )
        self._addFilter(filterDict)
    
    def clamp(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Clamps an image so the pixels with the specified extent are left unchanged but those at the boundary of the extent are extended outwards. This filter produces an image with infinite extent. You can use this filter when you need to blur an image but you want to avoid a soft, black fringe along the edges.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIClamp',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def CMYKHalftone(self, center: Point = (150.0, 150.0), width: float = 6.0, angle: float = 0.0, sharpness: float = 0.7, GCR: float = 1.0, UCR: float = 0.5):
        """
        Creates a color, halftoned rendition of the source image, using cyan, magenta, yellow, and black inks over a white page.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `width` a float. The distance between dots in the pattern.
        `angle` a float in degrees. The angle in degrees of the pattern.
        `sharpness` a float. The sharpness of the pattern. The larger the value, the sharper the pattern.
        `GCR` a float. The gray component replacement value. The value can vary from 0.0 (none) to 1.0.
        `UCR` a float. The under color removal value. The value can vary from 0.0 to 1.0. 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICMYKHalftone',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                width=width,
                angle=radians(angle),
                sharpness=sharpness,
                GCR=GCR,
                UCR=UCR
            )
        )
        self._addFilter(filterDict)
    
    def code128BarcodeGenerator(self, size: Size, message: str, quietSpace: float = 10.0, barcodeHeight: float = 32.0):
        """
        Generate a Code 128 barcode image for message data.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `message` a string. The message to encode in the Code 128 Barcode
        `quietSpace` a float. The number of empty white pixels that should surround the barcode.
        `barcodeHeight` a float. The height of the generated barcode in pixels.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICode128BarcodeGenerator',
            attributes=dict(
                message=AppKit.NSData.dataWithBytes_length_(message, len(message)),
                quietSpace=quietSpace,
                barcodeHeight=barcodeHeight
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def colorAbsoluteDifference(self, image2):
        """
        Produces an image that is the absolute value of the color difference between two images. The alpha channel of the result will be the product of the two image alpha channels.
        
        **Arguments:**
        
        `image2` a float. The second input image for differencing.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorAbsoluteDifference',
            attributes=dict(
                image2=image2
            )
        )
        self._addFilter(filterDict)
    
    def colorBlendMode(self, backgroundImage: Self):
        """
        Uses the luminance values of the background with the hue and saturation values of the source image. This mode preserves the gray levels in the image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def colorBurnBlendMode(self, backgroundImage: Self):
        """
        Darkens the background image samples to reflect the source image samples. Source image sample values that specify white do not produce a change.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorBurnBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def colorClamp(self, minComponents: BoundingBox = (0.0, 0.0, 0.0, 0.0), maxComponents: BoundingBox = (1.0, 1.0, 1.0, 1.0)):
        """
        Clamp color to a certain range.
        
        **Arguments:**
        
        `minComponents` a tuple (x, y, w, h). Lower clamping values.
        `maxComponents` a tuple (x, y, w, h). Higher clamping values.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorClamp',
            attributes=dict(
                minComponents=AppKit.CIVector.vectorWithValues_count_(minComponents, 4),
                maxComponents=AppKit.CIVector.vectorWithValues_count_(maxComponents, 4)
            )
        )
        self._addFilter(filterDict)
    
    def colorControls(self, saturation: float = 1.0, brightness: float = 0.0, contrast: float = 1.0):
        """
        Adjusts saturation, brightness, and contrast values.
        
        **Arguments:**
        
        `saturation` a float. The amount of saturation to apply. The larger the value, the more saturated the result.
        `brightness` a float. The amount of brightness to apply. The larger the value, the brighter the result.
        `contrast` a float. The amount of contrast to apply. The larger the value, the more contrast in the resulting image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorControls',
            attributes=dict(
                saturation=saturation,
                brightness=brightness,
                contrast=contrast
            )
        )
        self._addFilter(filterDict)
    
    def colorCrossPolynomial(self, redCoefficients: tuple = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), greenCoefficients: tuple = (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), blueCoefficients: tuple = (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)):
        """
        Adjusts the color of an image with polynomials.
        
        **Arguments:**
        
        `redCoefficients` a tuple (x, y, w, h). Polynomial coefficients for red channel.
        `greenCoefficients` a tuple (x, y, w, h). Polynomial coefficients for green channel.
        `blueCoefficients` a tuple (x, y, w, h). Polynomial coefficients for blue channel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorCrossPolynomial',
            attributes=dict(
                redCoefficients=AppKit.CIVector.vectorWithValues_count_(redCoefficients, 4),
                greenCoefficients=AppKit.CIVector.vectorWithValues_count_(greenCoefficients, 4),
                blueCoefficients=AppKit.CIVector.vectorWithValues_count_(blueCoefficients, 4)
            )
        )
        self._addFilter(filterDict)
    
    def colorCurves(self, colorSpace, curvesData: bytes | None = None, curvesDomain: Point = (0.0, 1.0)):
        """
        Uses a three-channel one-dimensional color table to transform the source image pixels.
        
        **Arguments:**
        
        `colorSpace` a CoreGraphics color space. The color space that defines the RGB values in the color table.
        `curvesData` a float. Data containing a color table of floating-point RGB values.
        `curvesDomain` a float. A two-element vector that defines the minimum and maximum RGB component values that are used to look up result values from the color table.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorCurves',
            attributes=dict(
                colorSpace=colorSpace,
                curvesData=curvesData,
                curvesDomain=curvesDomain
            )
        )
        self._addFilter(filterDict)
    
    def colorDodgeBlendMode(self, backgroundImage: Self):
        """
        Brightens the background image samples to reflect the source image samples. Source image sample values that specify black do not produce a change.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorDodgeBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def colorInvert(self):
        """
        Inverts the colors in an image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorInvert',
        )
        self._addFilter(filterDict)
    
    def colorMap(self, gradientImage: Self):
        """
        Performs a nonlinear transformation of source color values using mapping values provided in a table.
        
        **Arguments:**
        
        `gradientImage` an Image object. The image data from this image transforms the source image values.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorMap',
            attributes=dict(
                gradientImage=gradientImage
            )
        )
        self._addFilter(filterDict)
    
    def colorMatrix(self, RVector: BoundingBox = (1.0, 0.0, 0.0, 0.0), GVector: BoundingBox = (0.0, 1.0, 0.0, 0.0), BVector: BoundingBox = (0.0, 0.0, 1.0, 0.0), AVector: BoundingBox = (0.0, 0.0, 0.0, 1.0), biasVector: BoundingBox = (0.0, 0.0, 0.0, 0.0)):
        """
        Multiplies source color values and adds a bias factor to each color component.
        
        **Arguments:**
        
        `RVector` a tuple (x, y, w, h). The amount of red to multiply the source color values by.
        `GVector` a tuple (x, y, w, h). The amount of green to multiply the source color values by.
        `BVector` a tuple (x, y, w, h). The amount of blue to multiply the source color values by.
        `AVector` a tuple (x, y, w, h). The amount of alpha to multiply the source color values by.
        `biasVector` a tuple (x, y, w, h). A vector that’s added to each color component.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorMatrix',
            attributes=dict(
                RVector=AppKit.CIVector.vectorWithValues_count_(RVector, 4),
                GVector=AppKit.CIVector.vectorWithValues_count_(GVector, 4),
                BVector=AppKit.CIVector.vectorWithValues_count_(BVector, 4),
                AVector=AppKit.CIVector.vectorWithValues_count_(AVector, 4),
                biasVector=AppKit.CIVector.vectorWithValues_count_(biasVector, 4)
            )
        )
        self._addFilter(filterDict)
    
    def colorMonochrome(self, color: RGBAColorTuple = (0.6, 0.45, 0.3, 1.0), intensity: float = 1.0):
        """
        Remaps colors so they fall within shades of a single color.
        
        **Arguments:**
        
        `color` RGBA tuple Color (r, g, b, a). The monochrome color to apply to the image.
        `intensity` a float. The intensity of the monochrome effect. A value of 1.0 creates a monochrome image using the supplied color. A value of 0.0 has no effect on the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorMonochrome',
            attributes=dict(
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                intensity=intensity
            )
        )
        self._addFilter(filterDict)
    
    def colorPolynomial(self, redCoefficients: BoundingBox = (0.0, 1.0, 0.0, 0.0), greenCoefficients: BoundingBox = (0.0, 1.0, 0.0, 0.0), blueCoefficients: BoundingBox = (0.0, 1.0, 0.0, 0.0), alphaCoefficients: BoundingBox = (0.0, 1.0, 0.0, 0.0)):
        """
        Adjusts the color of an image with polynomials.
        
        **Arguments:**
        
        `redCoefficients` a tuple (x, y, w, h). Polynomial coefficients for red channel.
        `greenCoefficients` a tuple (x, y, w, h). Polynomial coefficients for green channel.
        `blueCoefficients` a tuple (x, y, w, h). Polynomial coefficients for blue channel.
        `alphaCoefficients` a tuple (x, y, w, h). Polynomial coefficients for alpha channel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorPolynomial',
            attributes=dict(
                redCoefficients=AppKit.CIVector.vectorWithValues_count_(redCoefficients, 4),
                greenCoefficients=AppKit.CIVector.vectorWithValues_count_(greenCoefficients, 4),
                blueCoefficients=AppKit.CIVector.vectorWithValues_count_(blueCoefficients, 4),
                alphaCoefficients=AppKit.CIVector.vectorWithValues_count_(alphaCoefficients, 4)
            )
        )
        self._addFilter(filterDict)
    
    def colorPosterize(self, levels: float = 6.0):
        """
        Remaps red, green, and blue color components to the number of brightness values you specify for each color component. This filter flattens colors to achieve a look similar to that of a silk-screened poster.
        
        **Arguments:**
        
        `levels` a float. The number of brightness levels to use for each color component. Lower values result in a more extreme poster effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorPosterize',
            attributes=dict(
                levels=levels
            )
        )
        self._addFilter(filterDict)
    
    def colorThreshold(self, threshold: float = 0.5):
        """
        Produces a binarized image from an image and a threshold value. The red, green and blue channels of the resulting image will be one if its value is greater than the threshold and zero otherwise.
        
        **Arguments:**
        
        `threshold` a float. The threshold value that governs if the RGB channels of the resulting image will be zero or one.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorThreshold',
            attributes=dict(
                threshold=threshold
            )
        )
        self._addFilter(filterDict)
    
    def colorThresholdOtsu(self):
        """
        Produces a binarized image from an image with finite extent. The threshold is calculated from the image histogram using Otsu’s method. The red, green and blue channels of the resulting image will be one if its value is greater than the threshold and zero otherwise.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColorThresholdOtsu',
        )
        self._addFilter(filterDict)
    
    def columnAverage(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Calculates the average color for each column of the specified area in an image, returning the result in a 1D image.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIColumnAverage',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def comicEffect(self):
        """
        Simulates a comic book drawing by outlining edges and applying a color halftone effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIComicEffect',
        )
        self._addFilter(filterDict)
    
    def constantColorGenerator(self, size: Size, color: RGBAColorTuple = (1.0, 0.0, 0.0, 1.0)):
        """
        Generates a solid color. You typically use the output of this filter as the input to another filter.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `color` RGBA tuple Color (r, g, b, a). The color to generate.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConstantColorGenerator',
            attributes=dict(
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def convertLabToRGB(self, normalize: bool = False):
        """
        Converts an image from La*b* color space to the Core Image RGB working space.
        
        **Arguments:**
        
        `normalize` a float. If normalize is false then the L channel is in the range 0 to 100 and the a*b* channels are in the range -128 to 128. If normalize is true then the La*b* channels are in the range 0 to 1.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvertLabToRGB',
            attributes=dict(
                normalize=normalize
            )
        )
        self._addFilter(filterDict)
    
    def convertRGBtoLab(self, normalize: bool = False):
        """
        Converts an image from the Core Image RGB working space to La*b* color space.
        
        **Arguments:**
        
        `normalize` a float. If normalize is false then the L channel is in the range 0 to 100 and the a*b* channels are in the range -128 to 128. If normalize is true then the La*b* channels are in the range 0 to 1.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvertRGBtoLab',
            attributes=dict(
                normalize=normalize
            )
        )
        self._addFilter(filterDict)
    
    def convolution3X3(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Convolution with 3 by 3 matrix.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 9 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGBA components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolution3X3',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolution5X5(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Convolution with 5 by 5 matrix.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 25 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGBA components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolution5X5',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolution7X7(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Convolution with 7 by 7 matrix.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 49 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGBA components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolution7X7',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolution9Horizontal(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Horizontal Convolution with 9 values.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 9 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGBA components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolution9Horizontal',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolution9Vertical(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Vertical Convolution with 9 values.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 9 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGBA components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolution9Vertical',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolutionRGB3X3(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Convolution of RGB channels with 3 by 3 matrix.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 9 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGB components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolutionRGB3X3',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolutionRGB5X5(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Convolution of RGB channels with 5 by 5 matrix.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 25 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGB components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolutionRGB5X5',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolutionRGB7X7(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Convolution of RGB channels with 7 by 7 matrix.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 49 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGB components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolutionRGB7X7',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolutionRGB9Horizontal(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Horizontal Convolution of RGB channels with 9 values.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 9 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGB components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolutionRGB9Horizontal',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def convolutionRGB9Vertical(self, weights: tuple = (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0), bias: float = 0.0):
        """
        Vertical Convolution of RGB channels with 9 values.
        
        **Arguments:**
        
        `weights` a float. A vector containing the 9 weights of the convolution kernel.
        `bias` a float. A value that is added to the RGB components of the output pixel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIConvolutionRGB9Vertical',
            attributes=dict(
                weights=weights,
                bias=bias
            )
        )
        self._addFilter(filterDict)
    
    def copyMachineTransition(self, targetImage: Self, extent: BoundingBox = (0.0, 0.0, 300.0, 300.0), color: RGBAColorTuple = (0.6, 1.0, 0.8, 1.0), time: float = 0.0, angle: float = 0.0, width: float = 200.0, opacity: float = 1.3):
        """
        Transitions from one image to another by simulating the effect of a copy machine.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `color` RGBA tuple Color (r, g, b, a). The color of the copier light.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `angle` a float in degrees. The angle in degrees of the copier light.
        `width` a float. The width of the copier light. 
        `opacity` a float. The opacity of the copier light. A value of 0.0 is transparent. A value of 1.0 is opaque.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICopyMachineTransition',
            attributes=dict(
                targetImage=targetImage,
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                time=time,
                angle=radians(angle),
                width=width,
                opacity=opacity
            )
        )
        self._addFilter(filterDict)
    
    def coreMLModelFilter(self, model, headIndex: float = 0.0, softmaxNormalization: bool = False):
        """
        Generates output image by applying input CoreML model to the input image.
        
        **Arguments:**
        
        `model` a float. The CoreML model to be used for applying effect on the image.
        `headIndex` a float. A number to specify which output of a multi-head CoreML model should be used for applying effect on the image.
        `softmaxNormalization` a float. A boolean value to specify that Softmax normalization should be applied to the output of the model.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICoreMLModelFilter',
            attributes=dict(
                model=model,
                headIndex=headIndex,
                softmaxNormalization=softmaxNormalization
            )
        )
        self._addFilter(filterDict)
    
    def crop(self, rectangle: BoundingBox = (-8.988465674311579e+307, -8.988465674311579e+307, 1.7976931348623157e+308, 1.7976931348623157e+308)):
        """
        Applies a crop to an image. The size and shape of the cropped image depend on the rectangle you specify.
        
        **Arguments:**
        
        `rectangle` a tuple (x, y, w, h). The rectangle that specifies the crop to apply to the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICrop',
            attributes=dict(
                rectangle=AppKit.CIVector.vectorWithValues_count_(rectangle, 4)
            )
        )
        self._addFilter(filterDict)
    
    def crystallize(self, radius: float = 20.0, center: Point = (150.0, 150.0)):
        """
        Creates polygon-shaped color blocks by aggregating source pixel-color values.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the effect. The larger the radius, the larger the resulting crystals.
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CICrystallize',
            attributes=dict(
                radius=radius,
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
            )
        )
        self._addFilter(filterDict)
    
    def darkenBlendMode(self, backgroundImage: Self):
        """
        Creates composite image samples by choosing the darker samples (from either the source image or the background). The result is that the background image samples are replaced by any source image samples that are darker. Otherwise, the background image samples are left unchanged.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDarkenBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def depthBlurEffect(self, disparityImage: Self, matteImage: Self, hairImage: Self, glassesImage: Self, gainMap: Self, focusRect, calibrationData, auxDataMetadata, shape, aperture: float = 0.0, leftEyePositions: Point = (-1.0, -1.0), rightEyePositions: Point = (-1.0, -1.0), chinPositions: Point = (-1.0, -1.0), nosePositions: Point = (-1.0, -1.0), lumaNoiseScale: float = 0.0, scaleFactor: float = 1.0):
        """
        Applies a variable radius disc blur to an image where areas in the background are softened more than those in the foreground.
        
        **Arguments:**
        
        `disparityImage` an Image object. 
        `matteImage` an Image object. A matting image.
        `hairImage` an Image object. A segmentation matte image that corresponds to people’s hair.
        `glassesImage` an Image object. A segmentation matte image that corresponds to people’s glasses.
        `gainMap` an Image object. 
        `focusRect` a float. 
        `calibrationData` a float. 
        `auxDataMetadata` a float. 
        `shape` a float. 
        `aperture` a float. 
        `leftEyePositions` a float. 
        `rightEyePositions` a float. 
        `chinPositions` a float. 
        `nosePositions` a float. 
        `lumaNoiseScale` a float. 
        `scaleFactor` a float. 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDepthBlurEffect',
            attributes=dict(
                disparityImage=disparityImage,
                matteImage=matteImage,
                hairImage=hairImage,
                glassesImage=glassesImage,
                gainMap=gainMap,
                focusRect=focusRect,
                calibrationData=calibrationData,
                auxDataMetadata=auxDataMetadata,
                shape=shape,
                aperture=aperture,
                leftEyePositions=leftEyePositions,
                rightEyePositions=rightEyePositions,
                chinPositions=chinPositions,
                nosePositions=nosePositions,
                lumaNoiseScale=lumaNoiseScale,
                scaleFactor=scaleFactor
            )
        )
        self._addFilter(filterDict)
    
    def depthOfField(self, point0: Point = (0.0, 300.0), point1: Point = (300.0, 300.0), saturation: float = 1.5, unsharpMaskRadius: float = 2.5, unsharpMaskIntensity: float = 0.5, radius: float = 6.0):
        """
        Simulates miniaturization effect created by Tilt & Shift lens by performing depth of field effects.
        
        **Arguments:**
        
        `point0` a tuple (x, y). 
        `point1` a tuple (x, y). 
        `saturation` a float. The amount to adjust the saturation.
        `unsharpMaskRadius` a float. 
        `unsharpMaskIntensity` a float. 
        `radius` a float. The distance from the center of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDepthOfField',
            attributes=dict(
                point0=AppKit.CIVector.vectorWithValues_count_(point0, 2),
                point1=AppKit.CIVector.vectorWithValues_count_(point1, 2),
                saturation=saturation,
                unsharpMaskRadius=unsharpMaskRadius,
                unsharpMaskIntensity=unsharpMaskIntensity,
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def depthToDisparity(self):
        """
        Convert a depth data image to disparity data.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDepthToDisparity',
        )
        self._addFilter(filterDict)
    
    def differenceBlendMode(self, backgroundImage: Self):
        """
        Subtracts either the source image sample color from the background image sample color, or the reverse, depending on which sample has the greater brightness value. Source image sample values that are black produce no change; white inverts the background color values.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDifferenceBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def discBlur(self, radius: float = 8.0):
        """
        Smooths an image using a disc-shaped convolution kernel.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the blur. The larger the radius, the blurrier the result.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDiscBlur',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def disintegrateWithMaskTransition(self, targetImage: Self, maskImage: Self, time: float = 0.0, shadowRadius: float = 8.0, shadowDensity: float = 0.65, shadowOffset: Point = (0.0, -10.0)):
        """
        Transitions from one image to another using the shape defined by a mask.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `maskImage` an Image object. An image that defines the shape to use when disintegrating from the source to the target image.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `shadowRadius` a float. The radius of the shadow created by the mask.
        `shadowDensity` a float. The density of the shadow created by the mask.
        `shadowOffset` a tuple (x, y). The offset of the shadow created by the mask.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDisintegrateWithMaskTransition',
            attributes=dict(
                targetImage=targetImage,
                maskImage=maskImage,
                time=time,
                shadowRadius=shadowRadius,
                shadowDensity=shadowDensity,
                shadowOffset=AppKit.CIVector.vectorWithValues_count_(shadowOffset, 2)
            )
        )
        self._addFilter(filterDict)
    
    def disparityToDepth(self):
        """
        Convert a disparity data image to depth data.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDisparityToDepth',
        )
        self._addFilter(filterDict)
    
    def displacementDistortion(self, displacementImage: Self, scale: float = 50.0):
        """
        Applies the grayscale values of the second image to the first image. The output image has a texture defined by the grayscale values.
        
        **Arguments:**
        
        `displacementImage` an Image object. An image whose grayscale values will be applied to the source image.
        `scale` a float. The amount of texturing of the resulting image. The larger the value, the greater the texturing.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDisplacementDistortion',
            attributes=dict(
                displacementImage=displacementImage,
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def dissolveTransition(self, targetImage: Self, time: float = 0.0):
        """
        Uses a dissolve to transition from one image to another.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDissolveTransition',
            attributes=dict(
                targetImage=targetImage,
                time=time
            )
        )
        self._addFilter(filterDict)
    
    def dither(self, intensity: float = 0.1):
        """
        Apply dithering to an image. This operation is usually performed in a perceptual color space.
        
        **Arguments:**
        
        `intensity` a float. The intensity of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDither',
            attributes=dict(
                intensity=intensity
            )
        )
        self._addFilter(filterDict)
    
    def divideBlendMode(self, backgroundImage: Self):
        """
        Divides the background image sample color from the source image sample color.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDivideBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def documentEnhancer(self, amount: float = 1.0):
        """
        Enhance a document image by removing unwanted shadows, whitening the background, and enhancing contrast.
        
        **Arguments:**
        
        `amount` a float. The amount of enhancement.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDocumentEnhancer',
            attributes=dict(
                amount=amount
            )
        )
        self._addFilter(filterDict)
    
    def dotScreen(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 6.0, sharpness: float = 0.7):
        """
        Simulates the dot patterns of a halftone screen.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the pattern.
        `width` a float. The distance between dots in the pattern.
        `sharpness` a float. The sharpness of the pattern. The larger the value, the sharper the pattern.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDotScreen',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width,
                sharpness=sharpness
            )
        )
        self._addFilter(filterDict)
    
    def droste(self, insetPoint0: Point = (200.0, 200.0), insetPoint1: Point = (400.0, 400.0), strands: float = 1.0, periodicity: float = 1.0, rotation: float = 0.0, zoom: float = 1.0):
        """
        Performs M.C. Escher Droste style deformation.
        
        **Arguments:**
        
        `insetPoint0` a tuple (x, y). 
        `insetPoint1` a tuple (x, y). 
        `strands` a float. 
        `periodicity` a float. 
        `rotation` a float. 
        `zoom` a float. 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIDroste',
            attributes=dict(
                insetPoint0=AppKit.CIVector.vectorWithValues_count_(insetPoint0, 2),
                insetPoint1=AppKit.CIVector.vectorWithValues_count_(insetPoint1, 2),
                strands=strands,
                periodicity=periodicity,
                rotation=rotation,
                zoom=zoom
            )
        )
        self._addFilter(filterDict)
    
    def edgePreserveUpsampleFilter(self, smallImage, spatialSigma: float = 3.0, lumaSigma: float = 0.15):
        """
        Upsamples a small image to the size of the input image using the luminance of the input image as a guide to preserve detail.
        
        **Arguments:**
        
        `smallImage` a float. 
        `spatialSigma` a float. 
        `lumaSigma` a float. 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIEdgePreserveUpsampleFilter',
            attributes=dict(
                smallImage=smallImage,
                spatialSigma=spatialSigma,
                lumaSigma=lumaSigma
            )
        )
        self._addFilter(filterDict)
    
    def edges(self, intensity: float = 1.0):
        """
        Finds all edges in an image and displays them in color.
        
        **Arguments:**
        
        `intensity` a float. The intensity of the edges. The larger the value, the higher the intensity.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIEdges',
            attributes=dict(
                intensity=intensity
            )
        )
        self._addFilter(filterDict)
    
    def edgeWork(self, radius: float = 3.0):
        """
        Produces a stylized black-and-white rendition of an image that looks similar to a woodblock cutout.
        
        **Arguments:**
        
        `radius` a float. The thickness of the edges. The larger the value, the thicker the edges.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIEdgeWork',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def eightfoldReflectedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0):
        """
        Produces a tiled image from a source image by applying an 8-way reflected symmetry.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIEightfoldReflectedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def exclusionBlendMode(self, backgroundImage: Self):
        """
        Produces an effect similar to that produced by the "Difference Blend Mode" filter but with lower contrast. Source image sample values that are black do not produce a change; white inverts the background color values.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIExclusionBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def exposureAdjust(self, EV: float = 0.0):
        """
        Adjusts the exposure setting for an image similar to the way you control exposure for a camera when you change the F-stop.
        
        **Arguments:**
        
        `EV` a float. The amount to adjust the exposure of the image by. The larger the value, the brighter the exposure.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIExposureAdjust',
            attributes=dict(
                EV=EV
            )
        )
        self._addFilter(filterDict)
    
    def falseColor(self, color0: RGBAColorTuple = (0.3, 0.0, 0.0, 1.0), color1: RGBAColorTuple = (1.0, 0.9, 0.8, 1.0)):
        """
        Maps luminance to a color ramp of two colors. False color is often used to process astronomical and other scientific data, such as ultraviolet and X-ray images.
        
        **Arguments:**
        
        `color0` RGBA tuple Color (r, g, b, a). The first color to use for the color ramp.
        `color1` RGBA tuple Color (r, g, b, a). The second color to use for the color ramp.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIFalseColor',
            attributes=dict(
                color0=AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3]),
                color1=AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
            )
        )
        self._addFilter(filterDict)
    
    def flashTransition(self, targetImage: Self, center: Point = (150.0, 150.0), extent: BoundingBox = (0.0, 0.0, 300.0, 300.0), color: RGBAColorTuple = (1.0, 0.8, 0.6, 1.0), time: float = 0.0, maxStriationRadius: float = 2.58, striationStrength: float = 0.5, striationContrast: float = 1.375, fadeThreshold: float = 0.85):
        """
        Transitions from one image to another by creating a flash. The flash originates from a point you specify. Small at first, it rapidly expands until the image frame is completely filled with the flash color. As the color fades, the target image begins to appear.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `extent` a tuple (x, y, w, h). The extent of the flash.
        `color` RGBA tuple Color (r, g, b, a). The color of the light rays emanating from the flash.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `maxStriationRadius` a float. The radius of the light rays emanating from the flash.
        `striationStrength` a float. The strength of the light rays emanating from the flash.
        `striationContrast` a float. The contrast of the light rays emanating from the flash.
        `fadeThreshold` a float. The amount of fade between the flash and the target image. The higher the value, the more flash time and the less fade time.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIFlashTransition',
            attributes=dict(
                targetImage=targetImage,
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                time=time,
                maxStriationRadius=maxStriationRadius,
                striationStrength=striationStrength,
                striationContrast=striationContrast,
                fadeThreshold=fadeThreshold
            )
        )
        self._addFilter(filterDict)
    
    def fourfoldReflectedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0, acuteAngle: float = 1.5707963267948966):
        """
        Produces a tiled image from a source image by applying a 4-way reflected symmetry.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        `acuteAngle` a float in degrees. The primary angle for the repeating reflected tile. Small values create thin diamond tiles, and higher values create fatter reflected tiles.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIFourfoldReflectedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width,
                acuteAngle=radians(acuteAngle)
            )
        )
        self._addFilter(filterDict)
    
    def fourfoldRotatedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0):
        """
        Produces a tiled image from a source image by rotating the source at increments of 90 degrees.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIFourfoldRotatedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def fourfoldTranslatedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0, acuteAngle: float = 1.5707963267948966):
        """
        Produces a tiled image from a source image by applying 4 translation operations.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        `acuteAngle` a float in degrees. The primary angle for the repeating translated tile. Small values create thin diamond tiles, and higher values create fatter translated tiles.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIFourfoldTranslatedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width,
                acuteAngle=radians(acuteAngle)
            )
        )
        self._addFilter(filterDict)
    
    def gaborGradients(self):
        """
        Applies multichannel 5 by 5 Gabor gradient filter to an image. The resulting image has maximum horizontal gradient in the red channel and the maximum vertical gradient in the green channel. The gradient values can be positive or negative.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGaborGradients',
        )
        self._addFilter(filterDict)
    
    def gammaAdjust(self, power: float = 1.0):
        """
        Adjusts midtone brightness. This filter is typically used to compensate for nonlinear effects of displays. Adjusting the gamma effectively changes the slope of the transition between black and white.
        
        **Arguments:**
        
        `power` a float. A gamma value to use to correct image brightness. The larger the value, the darker the result.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGammaAdjust',
            attributes=dict(
                power=power
            )
        )
        self._addFilter(filterDict)
    
    def gaussianBlur(self, radius: float = 10.0):
        """
        Spreads source pixels by an amount specified by a Gaussian distribution.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the blur. The larger the radius, the blurrier the result.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGaussianBlur',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def gaussianGradient(self, size: Size, center: Point = (150.0, 150.0), color0: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), color1: RGBAColorTuple = (0.0, 0.0, 0.0, 0.0), radius: float = 300.0):
        """
        Generates a gradient that varies from one color to another using a Gaussian distribution.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `color0` RGBA tuple Color (r, g, b, a). The first color to use in the gradient.
        `color1` RGBA tuple Color (r, g, b, a). The second color to use in the gradient.
        `radius` a float. The radius of the Gaussian distribution.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGaussianGradient',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                color0=AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3]),
                color1=AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3]),
                radius=radius
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def glassDistortion(self, texture: Self, center: Point = (150.0, 150.0), scale: float = 200.0):
        """
        Distorts an image by applying a glass-like texture. The raised portions of the output image are the result of applying a texture map.
        
        **Arguments:**
        
        `texture` an Image object. A texture to apply to the source image.
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `scale` a float. The amount of texturing of the resulting image. The larger the value, the greater the texturing.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGlassDistortion',
            attributes=dict(
                texture=texture,
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def glassLozenge(self, point0: Point = (150.0, 150.0), point1: Point = (350.0, 150.0), radius: float = 100.0, refraction: float = 1.7):
        """
        Creates a lozenge-shaped lens and distorts the portion of the image over which the lens is placed.
        
        **Arguments:**
        
        `point0` a tuple (x, y). The x and y position that defines the center of the circle at one end of the lozenge.
        `point1` a tuple (x, y). The x and y position that defines the center of the circle at the other end of the lozenge.
        `radius` a float. The radius of the lozenge. The larger the radius, the wider the extent of the distortion.
        `refraction` a float. The refraction of the glass.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGlassLozenge',
            attributes=dict(
                point0=AppKit.CIVector.vectorWithValues_count_(point0, 2),
                point1=AppKit.CIVector.vectorWithValues_count_(point1, 2),
                radius=radius,
                refraction=refraction
            )
        )
        self._addFilter(filterDict)
    
    def glideReflectedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0):
        """
        Produces a tiled image from a source image by translating and smearing the image.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGlideReflectedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def gloom(self, radius: float = 10.0, intensity: float = 0.5):
        """
        Dulls the highlights of an image.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the effect. The larger the radius, the greater the effect.
        `intensity` a float. The intensity of the effect. A value of 0.0 is no effect. A value of 1.0 is the maximum effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGloom',
            attributes=dict(
                radius=radius,
                intensity=intensity
            )
        )
        self._addFilter(filterDict)
    
    def guidedFilter(self, guideImage, radius: float = 1.0, epsilon: float = 0.0001):
        """
        Upsamples a small image to the size of the guide image using the content of the guide to preserve detail.
        
        **Arguments:**
        
        `guideImage` a float. A larger image to use as a guide.
        `radius` a float. The distance from the center of the effect.
        `epsilon` a float. 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIGuidedFilter',
            attributes=dict(
                guideImage=guideImage,
                radius=radius,
                epsilon=epsilon
            )
        )
        self._addFilter(filterDict)
    
    def hardLightBlendMode(self, backgroundImage: Self):
        """
        Either multiplies or screens colors, depending on the source image sample color. If the source image sample color is lighter than 50% gray, the background is lightened, similar to screening. If the source image sample color is darker than 50% gray, the background is darkened, similar to multiplying. If the source image sample color is equal to 50% gray, the source image is not changed. Image samples that are equal to pure black or pure white result in pure black or white. The overall effect is similar to what you would achieve by shining a harsh spotlight on the source image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHardLightBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def hatchedScreen(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 6.0, sharpness: float = 0.7):
        """
        Simulates the hatched pattern of a halftone screen.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the pattern.
        `width` a float. The distance between lines in the pattern.
        `sharpness` a float. The amount of sharpening to apply.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHatchedScreen',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width,
                sharpness=sharpness
            )
        )
        self._addFilter(filterDict)
    
    def heightFieldFromMask(self, radius: float = 10.0):
        """
        Produces a continuous three-dimensional, loft-shaped height field from a grayscale mask. The white values of the mask define those pixels that are inside the height field while the black values define those pixels that are outside. The field varies smoothly and continuously inside the mask, reaching the value 0 at the edge of the mask. You can use this filter with the Shaded Material filter to produce extremely realistic shaded objects.
        
        **Arguments:**
        
        `radius` a float. The distance from the edge of the mask for the smooth transition is proportional to the input radius. Larger values make the transition smoother and more pronounced. Smaller values make the transition approximate a fillet radius.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHeightFieldFromMask',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def hexagonalPixellate(self, center: Point = (150.0, 150.0), scale: float = 8.0):
        """
        Displays an image as colored hexagons whose color is an average of the pixels they replace.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `scale` a float. The scale determines the size of the hexagons. Larger values result in larger hexagons.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHexagonalPixellate',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def highlightShadowAdjust(self, radius: float = 0.0, shadowAmount: float = 0.0, highlightAmount: float = 1.0):
        """
        Adjust the tonal mapping of an image while preserving spatial detail.
        
        **Arguments:**
        
        `radius` a float. Shadow Highlight Radius.
        `shadowAmount` a float. The amount of adjustment to the shadows of the image.
        `highlightAmount` a float. The amount of adjustment to the highlights of the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHighlightShadowAdjust',
            attributes=dict(
                radius=radius,
                shadowAmount=shadowAmount,
                highlightAmount=highlightAmount
            )
        )
        self._addFilter(filterDict)
    
    def histogramDisplayFilter(self, height: float = 100.0, highLimit: float = 1.0, lowLimit: float = 0.0):
        """
        Generates a displayable histogram image from the output of the "Area Histogram" filter.
        
        **Arguments:**
        
        `height` a float. The height of the displayable histogram image.
        `highLimit` a float. The fraction of the right portion of the histogram image to make lighter.
        `lowLimit` a float. The fraction of the left portion of the histogram image to make darker.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHistogramDisplayFilter',
            attributes=dict(
                height=height,
                highLimit=highLimit,
                lowLimit=lowLimit
            )
        )
        self._addFilter(filterDict)
    
    def holeDistortion(self, center: Point = (150.0, 150.0), radius: float = 150.0):
        """
        Creates a circular area that pushes the image pixels outward, distorting those pixels closest to the circle the most.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHoleDistortion',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def hueAdjust(self, angle: float = 0.0):
        """
        Changes the overall hue, or tint, of the source pixels.
        
        **Arguments:**
        
        `angle` a float in degrees. An angle in degrees to use to correct the hue of an image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHueAdjust',
            attributes=dict(
                angle=radians(angle)
            )
        )
        self._addFilter(filterDict)
    
    def hueBlendMode(self, backgroundImage: Self):
        """
        Uses the luminance and saturation values of the background with the hue of the source image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHueBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def hueSaturationValueGradient(self, value: float = 1.0, radius: float = 300.0, softness: float = 1.0, dither: float = 1.0, colorSpace = None):
        """
        Generates a color wheel that shows hues and saturations for a specified value.
        
        **Arguments:**
        
        `value` a float. The color value used to generate the color wheel.
        `radius` a float. The distance from the center of the effect.
        `softness` a float. 
        `dither` a float. 
        `colorSpace` a CoreGraphics color space. The color space that the color wheel should be generated in.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIHueSaturationValueGradient',
            attributes=dict(
                value=value,
                radius=radius,
                softness=softness,
                dither=dither,
                colorSpace=colorSpace
            )
        )
        self._addFilter(filterDict)
    
    def kaleidoscope(self, count: float = 6.0, center: Point = (150.0, 150.0), angle: float = 0.0):
        """
        Produces a kaleidoscopic image from a source image by applying 12-way symmetry.
        
        **Arguments:**
        
        `count` a float. The number of reflections in the pattern.
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of reflection.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIKaleidoscope',
            attributes=dict(
                count=count,
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle)
            )
        )
        self._addFilter(filterDict)
    
    def keystoneCorrectionCombined(self, topLeft, topRight, bottomRight, bottomLeft, focalLength: float = 28.0):
        """
        Apply keystone correction to an image with combined horizontal and vertical guides.
        
        **Arguments:**
        
        `topLeft` a tuple (x, y). The top left coordinate of the guide.
        `topRight` a tuple (x, y). The top right coordinate of the guide.
        `bottomRight` a tuple (x, y). The bottom right coordinate of the guide.
        `bottomLeft` a tuple (x, y). The bottom left coordinate of the guide.
        `focalLength` a float. 35mm equivalent focal length of the input image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIKeystoneCorrectionCombined',
            attributes=dict(
                topLeft=AppKit.CIVector.vectorWithValues_count_(topLeft, 2),
                topRight=AppKit.CIVector.vectorWithValues_count_(topRight, 2),
                bottomRight=AppKit.CIVector.vectorWithValues_count_(bottomRight, 2),
                bottomLeft=AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2),
                focalLength=focalLength
            )
        )
        self._addFilter(filterDict)
    
    def keystoneCorrectionHorizontal(self, topLeft, topRight, bottomRight, bottomLeft, focalLength: float = 28.0):
        """
        Apply horizontal keystone correction to an image with guides.
        
        **Arguments:**
        
        `topLeft` a tuple (x, y). The top left coordinate of the guide.
        `topRight` a tuple (x, y). The top right coordinate of the guide.
        `bottomRight` a tuple (x, y). The bottom right coordinate of the guide.
        `bottomLeft` a tuple (x, y). The bottom left coordinate of the guide.
        `focalLength` a float. 35mm equivalent focal length of the input image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIKeystoneCorrectionHorizontal',
            attributes=dict(
                topLeft=AppKit.CIVector.vectorWithValues_count_(topLeft, 2),
                topRight=AppKit.CIVector.vectorWithValues_count_(topRight, 2),
                bottomRight=AppKit.CIVector.vectorWithValues_count_(bottomRight, 2),
                bottomLeft=AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2),
                focalLength=focalLength
            )
        )
        self._addFilter(filterDict)
    
    def keystoneCorrectionVertical(self, topLeft, topRight, bottomRight, bottomLeft, focalLength: float = 28.0):
        """
        Apply vertical keystone correction to an image with guides.
        
        **Arguments:**
        
        `topLeft` a tuple (x, y). The top left coordinate of the guide.
        `topRight` a tuple (x, y). The top right coordinate of the guide.
        `bottomRight` a tuple (x, y). The bottom right coordinate of the guide.
        `bottomLeft` a tuple (x, y). The bottom left coordinate of the guide.
        `focalLength` a float. 35mm equivalent focal length of the input image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIKeystoneCorrectionVertical',
            attributes=dict(
                topLeft=AppKit.CIVector.vectorWithValues_count_(topLeft, 2),
                topRight=AppKit.CIVector.vectorWithValues_count_(topRight, 2),
                bottomRight=AppKit.CIVector.vectorWithValues_count_(bottomRight, 2),
                bottomLeft=AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2),
                focalLength=focalLength
            )
        )
        self._addFilter(filterDict)
    
    def KMeans(self, means, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0), count: float = 8.0, passes: float = 5.0, perceptual: bool = False):
        """
        Create a palette of the most common colors found in the image.
        
        **Arguments:**
        
        `means` a float. Specifies the color seeds to use for k-means clustering, either passed as an image or an array of colors.
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `count` a float. Specifies how many k-means color clusters should be used.
        `passes` a float. Specifies how many k-means passes should be performed.
        `perceptual` a float. Specifies whether the k-means color palette should be computed in a perceptual color space.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIKMeans',
            attributes=dict(
                means=means,
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                count=count,
                passes=passes,
                perceptual=perceptual
            )
        )
        self._addFilter(filterDict)
    
    def labDeltaE(self, image2):
        """
        Produces an image with the Lab ∆E difference values between two images. The result image will contain ∆E 1994 values between 0.0 and 100.0 where 2.0 is considered a just noticeable difference.
        
        **Arguments:**
        
        `image2` a float. The second input image for comparison.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILabDeltaE',
            attributes=dict(
                image2=image2
            )
        )
        self._addFilter(filterDict)
    
    def lanczosScaleTransform(self, scale: float = 1.0, aspectRatio: float = 1.0):
        """
        Produces a high-quality, scaled version of a source image. You typically use this filter to scale down an image.
        
        **Arguments:**
        
        `scale` a float. The scaling factor to use on the image. Values less than 1.0 scale down the images. Values greater than 1.0 scale up the image.
        `aspectRatio` a float. The additional horizontal scaling factor to use on the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILanczosScaleTransform',
            attributes=dict(
                scale=scale,
                aspectRatio=aspectRatio
            )
        )
        self._addFilter(filterDict)
    
    def lenticularHaloGenerator(self, size: Size, center: Point = (150.0, 150.0), color: RGBAColorTuple = (1.0, 0.9, 0.8, 1.0), haloRadius: float = 70.0, haloWidth: float = 87.0, haloOverlap: float = 0.77, striationStrength: float = 0.5, striationContrast: float = 1.0, time: float = 0.0):
        """
        Simulates a halo that is generated by the diffraction associated with the spread of a lens. This filter is typically applied to another image to simulate lens flares and similar effects.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `color` RGBA tuple Color (r, g, b, a). A color.
        `haloRadius` a float. The radius of the halo.
        `haloWidth` a float. The width of the halo, from its inner radius to its outer radius.
        `haloOverlap` a float. 
        `striationStrength` a float. The intensity of the halo colors. Larger values are more intense.
        `striationContrast` a float. The contrast of the halo colors. Larger values are higher contrast.
        `time` a float. The duration of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILenticularHaloGenerator',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                haloRadius=haloRadius,
                haloWidth=haloWidth,
                haloOverlap=haloOverlap,
                striationStrength=striationStrength,
                striationContrast=striationContrast,
                time=time
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def lightenBlendMode(self, backgroundImage: Self):
        """
        Creates composite image samples by choosing the lighter samples (either from the source image or the background). The result is that the background image samples are replaced by any source image samples that are lighter. Otherwise, the background image samples are left unchanged.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILightenBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def lightTunnel(self, center: Point = (150.0, 150.0), rotation: float = 0.0, radius: float = 100.0):
        """
        Light tunnel distortion.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `rotation` a float. Rotation angle in degrees of the light tunnel.
        `radius` a float. Center radius of the light tunnel.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILightTunnel',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                rotation=rotation,
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def linearBurnBlendMode(self, backgroundImage: Self):
        """
        Inverts the unpremultiplied source and background image sample color, inverts the sum, and then blends the result with the background according to the PDF basic compositing formula. Source image values that are white produce no change. Source image values that are black invert the background color values.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILinearBurnBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def linearDodgeBlendMode(self, backgroundImage: Self):
        """
        Unpremultiplies the source and background image sample colors, adds them, and then blends the result with the background according to the PDF basic compositing formula. Source image values that are black produces output that is the same as the background. Source image values that are non-black brighten the background color values.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILinearDodgeBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def linearGradient(self, size: Size, point0: Point = (0.0, 0.0), point1: Point = (200.0, 200.0), color0: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), color1: RGBAColorTuple = (0.0, 0.0, 0.0, 1.0)):
        """
        Generates a gradient that varies along a linear axis between two defined endpoints.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `point0` a tuple (x, y). The starting position of the gradient -- where the first color begins.
        `point1` a tuple (x, y). The ending position of the gradient -- where the second color begins.
        `color0` RGBA tuple Color (r, g, b, a). The first color to use in the gradient.
        `color1` RGBA tuple Color (r, g, b, a). The second color to use in the gradient.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILinearGradient',
            attributes=dict(
                point0=AppKit.CIVector.vectorWithValues_count_(point0, 2),
                point1=AppKit.CIVector.vectorWithValues_count_(point1, 2),
                color0=AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3]),
                color1=AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def linearLightBlendMode(self, backgroundImage: Self):
        """
        A blend mode that is a combination of linear burn and linear dodge blend modes.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILinearLightBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def linearToSRGBToneCurve(self):
        """
        Converts an image in linear space to sRGB space.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILinearToSRGBToneCurve',
        )
        self._addFilter(filterDict)
    
    def lineOverlay(self, NRNoiseLevel: float = 0.07, NRSharpness: float = 0.71, edgeIntensity: float = 1.0, threshold: float = 0.1, contrast: float = 50.0):
        """
        Creates a sketch that outlines the edges of an image in black, leaving the non-outlined portions of the image transparent. The result has alpha and is rendered in black, so it won’t look like much until you render it over another image using source over compositing.
        
        **Arguments:**
        
        `NRNoiseLevel` a float. The noise level of the image (used with camera data) that gets removed before tracing the edges of the image. Increasing the noise level helps to clean up the traced edges of the image.
        `NRSharpness` a float. The amount of sharpening done when removing noise in the image before tracing the edges of the image. This improves the edge acquisition.
        `edgeIntensity` a float. The accentuation factor of the Sobel gradient information when tracing the edges of the image. Higher values find more edges, although typically a low value (such as 1.0) is used.
        `threshold` a float. This value determines edge visibility. Larger values thin out the edges.
        `contrast` a float. The amount of anti-aliasing to use on the edges produced by this filter. Higher values produce higher contrast edges (they are less anti-aliased).
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILineOverlay',
            attributes=dict(
                NRNoiseLevel=NRNoiseLevel,
                NRSharpness=NRSharpness,
                edgeIntensity=edgeIntensity,
                threshold=threshold,
                contrast=contrast
            )
        )
        self._addFilter(filterDict)
    
    def lineScreen(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 6.0, sharpness: float = 0.7):
        """
        Simulates the line pattern of a halftone screen.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the pattern.
        `width` a float. The distance between lines in the pattern.
        `sharpness` a float. The sharpness of the pattern. The larger the value, the sharper the pattern.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILineScreen',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width,
                sharpness=sharpness
            )
        )
        self._addFilter(filterDict)
    
    def luminosityBlendMode(self, backgroundImage: Self):
        """
        Uses the hue and saturation of the background with the luminance of the source image. This mode creates an effect that is inverse to the effect created by the "Color Blend Mode" filter.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CILuminosityBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def maskedVariableBlur(self, mask: Self, radius: float = 5.0):
        """
        Blurs an image according to the brightness levels in a mask image.
        
        **Arguments:**
        
        `mask` an Image object. The mask image that determines how much to blur the image. The mask’s green channel value from 0.0 to 1.0 determines if the image is not blurred or blurred by the full radius.
        `radius` a float. A value that governs the maximum blur radius to apply.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMaskedVariableBlur',
            attributes=dict(
                mask=mask._ciImage(),
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def maskToAlpha(self):
        """
        Converts a grayscale image to a white image that is masked by alpha. The white values from the source image produce the inside of the mask; the black values become completely transparent.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMaskToAlpha',
        )
        self._addFilter(filterDict)
    
    def maximumComponent(self):
        """
        Converts an image to grayscale using the maximum of the three color components.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMaximumComponent',
        )
        self._addFilter(filterDict)
    
    def maximumCompositing(self, backgroundImage: Self):
        """
        Computes the maximum value, by color component, of two input images and creates an output image using the maximum values. This is similar to dodging.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMaximumCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def meshGenerator(self, size: Size, mesh, width: float = 1.5, color: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0)):
        """
        Generates a mesh from an array of line segments.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `mesh` a float. An array of line segments stored as an array of CIVectors each containing a start point and end point.
        `width` a float. The width in pixels of the effect.
        `color` RGBA tuple Color (r, g, b, a). A color.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMeshGenerator',
            attributes=dict(
                mesh=mesh,
                width=width,
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def minimumComponent(self):
        """
        Converts an image to grayscale using the minimum of the three color components.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMinimumComponent',
        )
        self._addFilter(filterDict)
    
    def minimumCompositing(self, backgroundImage: Self):
        """
        Computes the minimum value, by color component, of two input images and creates an output image using the minimum values. This is similar to burning.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMinimumCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def mix(self, backgroundImage: Self, amount: float = 1.0):
        """
        Uses an amount parameter to interpolate between an image and a background image. When value is 0.0 or less, the result is the background image. When the value is 1.0 or more, the result is the image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        `amount` a float. The amount of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMix',
            attributes=dict(
                backgroundImage=backgroundImage,
                amount=amount
            )
        )
        self._addFilter(filterDict)
    
    def modTransition(self, targetImage: Self, center: Point = (150.0, 150.0), time: float = 0.0, angle: float = 2.0, radius: float = 150.0, compression: float = 300.0):
        """
        Transitions from one image to another by revealing the target image through irregularly shaped holes.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `angle` a float in degrees. The angle in degrees of the mod hole pattern.
        `radius` a float. The radius of the undistorted holes in the pattern.
        `compression` a float. The amount of stretching applied to the mod hole pattern. Holes in the center are not distorted as much as those at the edge of the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIModTransition',
            attributes=dict(
                targetImage=targetImage,
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                time=time,
                angle=radians(angle),
                radius=radius,
                compression=compression
            )
        )
        self._addFilter(filterDict)
    
    def morphologyGradient(self, radius: float = 5.0):
        """
        Finds the edges of an image by returning the difference between the morphological minimum and maximum operations to the image.
        
        **Arguments:**
        
        `radius` a float. The desired radius of the circular morphological operation to the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMorphologyGradient',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def morphologyMaximum(self, radius: float = 0.0):
        """
        Lightens areas of an image by applying a circular morphological maximum operation to the image.
        
        **Arguments:**
        
        `radius` a float. The desired radius of the circular morphological operation to the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMorphologyMaximum',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def morphologyMinimum(self, radius: float = 0.0):
        """
        Darkens areas of an image by applying a circular morphological maximum operation to the image.
        
        **Arguments:**
        
        `radius` a float. The desired radius of the circular morphological operation to the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMorphologyMinimum',
            attributes=dict(
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def morphologyRectangleMaximum(self, width: float = 5.0, height: float = 5.0):
        """
        Lightens areas of an image by applying a rectangular morphological maximum operation to the image.
        
        **Arguments:**
        
        `width` a float. The width in pixels of the morphological operation. The value will be rounded to the nearest odd integer.
        `height` a float. The height in pixels of the morphological operation. The value will be rounded to the nearest odd integer.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMorphologyRectangleMaximum',
            attributes=dict(
                width=width,
                height=height
            )
        )
        self._addFilter(filterDict)
    
    def morphologyRectangleMinimum(self, width: float = 5.0, height: float = 5.0):
        """
        Darkens areas of an image by applying a rectangular morphological maximum operation to the image.
        
        **Arguments:**
        
        `width` a float. The width in pixels of the morphological operation. The value will be rounded to the nearest odd integer.
        `height` a float. The height in pixels of the morphological operation. The value will be rounded to the nearest odd integer.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMorphologyRectangleMinimum',
            attributes=dict(
                width=width,
                height=height
            )
        )
        self._addFilter(filterDict)
    
    def motionBlur(self, radius: float = 20.0, angle: float = 0.0):
        """
        Blurs an image to simulate the effect of using a camera that moves a specified angle and distance while capturing the image.
        
        **Arguments:**
        
        `radius` a float. The radius determines how many pixels are used to create the blur. The larger the radius, the blurrier the result.
        `angle` a float in degrees. The angle in degrees of the motion determines which direction the blur smears.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMotionBlur',
            attributes=dict(
                radius=radius,
                angle=radians(angle)
            )
        )
        self._addFilter(filterDict)
    
    def multiplyBlendMode(self, backgroundImage: Self):
        """
        Multiplies the source image samples with the background image samples. This results in colors that are at least as dark as either of the two contributing sample colors.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMultiplyBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def multiplyCompositing(self, backgroundImage: Self):
        """
        Multiplies the color component of two input images and creates an output image using the multiplied values. This filter is typically used to add a spotlight or similar lighting effect to an image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIMultiplyCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def ninePartStretched(self, breakpoint0: Point = (50.0, 50.0), breakpoint1: Point = (150.0, 150.0), growAmount: Point = (100.0, 100.0)):
        """
        Distorts an image by stretching an image based on two input breakpoints.
        
        **Arguments:**
        
        `breakpoint0` a float. Lower left corner of image to retain before stretching begins.
        `breakpoint1` a float. Upper right corner of image to retain after stretching ends.
        `growAmount` a float. Vector indicating how much image should grow in pixels in both dimensions.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CINinePartStretched',
            attributes=dict(
                breakpoint0=breakpoint0,
                breakpoint1=breakpoint1,
                growAmount=growAmount
            )
        )
        self._addFilter(filterDict)
    
    def ninePartTiled(self, breakpoint0: Point = (50.0, 50.0), breakpoint1: Point = (150.0, 150.0), growAmount: Point = (100.0, 100.0), flipYTiles: bool = True):
        """
        Distorts an image by tiling an image based on two input breakpoints.
        
        **Arguments:**
        
        `breakpoint0` a float. Lower left corner of image to retain before tiling begins.
        `breakpoint1` a float. Upper right corner of image to retain after tiling ends.
        `growAmount` a float. Vector indicating how much image should grow in pixels in both dimensions.
        `flipYTiles` a float. Indicates that Y-Axis flip should occur.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CINinePartTiled',
            attributes=dict(
                breakpoint0=breakpoint0,
                breakpoint1=breakpoint1,
                growAmount=growAmount,
                flipYTiles=flipYTiles
            )
        )
        self._addFilter(filterDict)
    
    def noiseReduction(self, noiseLevel: float = 0.02, sharpness: float = 0.4):
        """
        Reduces noise using a threshold value to define what is considered noise. Small changes in luminance below that value are considered noise and get a noise reduction treatment, which is a local blur. Changes above the threshold value are considered edges, so they are sharpened.
        
        **Arguments:**
        
        `noiseLevel` a float. The amount of noise reduction. The larger the value, the more noise reduction.
        `sharpness` a float. The sharpness of the final image. The larger the value, the sharper the result.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CINoiseReduction',
            attributes=dict(
                noiseLevel=noiseLevel,
                sharpness=sharpness
            )
        )
        self._addFilter(filterDict)
    
    def opTile(self, center: Point = (150.0, 150.0), scale: float = 2.8, angle: float = 0.0, width: float = 65.0):
        """
        Segments an image, applying any specified scaling and rotation, and then assembles the image again to give an op art appearance.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `scale` a float. The scale determines the number of tiles in the effect.
        `angle` a float in degrees. The angle in degrees of a tile.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIOpTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                scale=scale,
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def overlayBlendMode(self, backgroundImage: Self):
        """
        Either multiplies or screens the source image samples with the background image samples, depending on the background color. The result is to overlay the existing image samples while preserving the highlights and shadows of the background. The background color mixes with the source image to reflect the lightness or darkness of the background.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIOverlayBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def pageCurlTransition(self, targetImage: Self, backsideImage: Self, shadingImage: Self, extent: BoundingBox = (0.0, 0.0, 300.0, 300.0), time: float = 0.0, angle: float = 0.0, radius: float = 100.0):
        """
        Transitions from one image to another by simulating a curling page, revealing the new image as the page curls.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `backsideImage` an Image object. The image that appears on the back of the source image, as the page curls to reveal the target image.
        `shadingImage` an Image object. An image that looks like a shaded sphere enclosed in a square image.
        `extent` a tuple (x, y, w, h). The extent of the effect.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `angle` a float in degrees. The angle in degrees of the curling page.
        `radius` a float. The radius of the curl.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPageCurlTransition',
            attributes=dict(
                targetImage=targetImage,
                backsideImage=backsideImage,
                shadingImage=shadingImage,
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                time=time,
                angle=radians(angle),
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def pageCurlWithShadowTransition(self, targetImage: Self, backsideImage: Self, extent: BoundingBox = (0.0, 0.0, 0.0, 0.0), time: float = 0.0, angle: float = 0.0, radius: float = 100.0, shadowSize: float = 0.5, shadowAmount: float = 0.7, shadowExtent: BoundingBox = (0.0, 0.0, 0.0, 0.0)):
        """
        Transitions from one image to another by simulating a curling page, revealing the new image as the page curls.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `backsideImage` an Image object. The image that appears on the back of the source image, as the page curls to reveal the target image.
        `extent` a tuple (x, y, w, h). The extent of the effect.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `angle` a float in degrees. The angle in degrees of the curling page.
        `radius` a float. The radius of the curl.
        `shadowSize` a float. The maximum size in pixels of the shadow.
        `shadowAmount` a float. The strength of the shadow.
        `shadowExtent` a tuple (x, y, w, h). The rectagular portion of input image that will cast a shadow.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPageCurlWithShadowTransition',
            attributes=dict(
                targetImage=targetImage,
                backsideImage=backsideImage,
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                time=time,
                angle=radians(angle),
                radius=radius,
                shadowSize=shadowSize,
                shadowAmount=shadowAmount,
                shadowExtent=AppKit.CIVector.vectorWithValues_count_(shadowExtent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def paletteCentroid(self, paletteImage, perceptual: bool = False):
        """
        Calculate the mean (x,y) image coordinates of a color palette.
        
        **Arguments:**
        
        `paletteImage` a float. The input color palette, obtained using "CIKMeans" filter.
        `perceptual` a float. Specifies whether the color palette should be applied in a perceptual color space.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPaletteCentroid',
            attributes=dict(
                paletteImage=paletteImage,
                perceptual=perceptual
            )
        )
        self._addFilter(filterDict)
    
    def palettize(self, paletteImage, perceptual: bool = False):
        """
        Paint an image from a color palette obtained using "CIKMeans".
        
        **Arguments:**
        
        `paletteImage` a float. The input color palette, obtained using "CIKMeans" filter.
        `perceptual` a float. Specifies whether the color palette should be applied in a perceptual color space.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPalettize',
            attributes=dict(
                paletteImage=paletteImage,
                perceptual=perceptual
            )
        )
        self._addFilter(filterDict)
    
    def parallelogramTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, acuteAngle: float = 1.5707963267948966, width: float = 100.0):
        """
        Warps an image by reflecting it in a parallelogram, and then tiles the result.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `acuteAngle` a float in degrees. The primary angle for the repeating parallelogram tile. Small values create thin diamond tiles, and higher values create fatter parallelogram tiles.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIParallelogramTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                acuteAngle=radians(acuteAngle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def PDF417BarcodeGenerator(self, size: Size, message: str, minWidth, maxWidth, minHeight, maxHeight, dataColumns, rows, preferredAspectRatio, compactionMode, compactStyle, correctionLevel, alwaysSpecifyCompaction):
        """
        Generate a PDF417 barcode image for message data.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `message` a string. The message to encode in the PDF417 Barcode
        `minWidth` a float. The minimum width of the generated barcode in pixels.
        `maxWidth` a float. The maximum width of the generated barcode in pixels.
        `minHeight` a float. The minimum height of the generated barcode in pixels.
        `maxHeight` a float. The maximum height of the generated barcode in pixels.
        `dataColumns` a float. The number of data columns in the generated barcode
        `rows` a float. The number of rows in the generated barcode
        `preferredAspectRatio` a float. The preferred aspect ratio of the generated barcode
        `compactionMode` a float. The compaction mode of the generated barcode.
        `compactStyle` a bool. Force a compact style Aztec code to `True` or `False`. Set to `None` for automatic.
        `correctionLevel` a float. The correction level ratio of the generated barcode
        `alwaysSpecifyCompaction` a bool. Force compaction style to `True` or `False`. Set to `None` for automatic.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPDF417BarcodeGenerator',
            attributes=dict(
                message=AppKit.NSData.dataWithBytes_length_(message, len(message)),
                minWidth=minWidth,
                maxWidth=maxWidth,
                minHeight=minHeight,
                maxHeight=maxHeight,
                dataColumns=dataColumns,
                rows=rows,
                preferredAspectRatio=preferredAspectRatio,
                compactionMode=compactionMode,
                compactStyle=compactStyle,
                correctionLevel=correctionLevel,
                alwaysSpecifyCompaction=alwaysSpecifyCompaction
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def personSegmentation(self, qualityLevel: float = 0.0):
        """
        Returns a segmentation mask that is red in the portions of an image that are likely to be persons. The returned image may have a different size and aspect ratio from the input image.
        
        **Arguments:**
        
        `qualityLevel` a float. Determines the size and quality of the resulting segmentation mask. The value can be a number where 0 is accurate, 1 is balanced, and 2 is fast.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPersonSegmentation',
            attributes=dict(
                qualityLevel=qualityLevel
            )
        )
        self._addFilter(filterDict)
    
    def perspectiveCorrection(self, topLeft: Point = (118.0, 484.0), topRight: Point = (646.0, 507.0), bottomRight: Point = (548.0, 140.0), bottomLeft: Point = (155.0, 153.0), crop: bool = True):
        """
        Apply a perspective correction to an image.
        
        **Arguments:**
        
        `topLeft` a tuple (x, y). The top left coordinate to be perspective corrected.
        `topRight` a tuple (x, y). The top right coordinate to be perspective corrected.
        `bottomRight` a tuple (x, y). The bottom right coordinate to be perspective corrected.
        `bottomLeft` a tuple (x, y). The bottom left coordinate to be perspective corrected.
        `crop` a float. 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPerspectiveCorrection',
            attributes=dict(
                topLeft=AppKit.CIVector.vectorWithValues_count_(topLeft, 2),
                topRight=AppKit.CIVector.vectorWithValues_count_(topRight, 2),
                bottomRight=AppKit.CIVector.vectorWithValues_count_(bottomRight, 2),
                bottomLeft=AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2),
                crop=crop
            )
        )
        self._addFilter(filterDict)
    
    def perspectiveRotate(self, focalLength: float = 28.0, pitch: float = 0.0, yaw: float = 0.0, roll: float = 0.0):
        """
        Apply a homogenous rotation transform to an image.
        
        **Arguments:**
        
        `focalLength` a float. 35mm equivalent focal length of the input image.
        `pitch` a float. Pitch angle in degrees.
        `yaw` a float. Yaw angle in degrees.
        `roll` a float. Roll angle in degrees.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPerspectiveRotate',
            attributes=dict(
                focalLength=focalLength,
                pitch=pitch,
                yaw=yaw,
                roll=roll
            )
        )
        self._addFilter(filterDict)
    
    def perspectiveTile(self, topLeft: Point = (118.0, 484.0), topRight: Point = (646.0, 507.0), bottomRight: Point = (548.0, 140.0), bottomLeft: Point = (155.0, 153.0)):
        """
        Applies a perspective transform to an image and then tiles the result.
        
        **Arguments:**
        
        `topLeft` a tuple (x, y). The top left coordinate of a tile.
        `topRight` a tuple (x, y). The top right coordinate of a tile.
        `bottomRight` a tuple (x, y). The bottom right coordinate of a tile.
        `bottomLeft` a tuple (x, y). The bottom left coordinate of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPerspectiveTile',
            attributes=dict(
                topLeft=AppKit.CIVector.vectorWithValues_count_(topLeft, 2),
                topRight=AppKit.CIVector.vectorWithValues_count_(topRight, 2),
                bottomRight=AppKit.CIVector.vectorWithValues_count_(bottomRight, 2),
                bottomLeft=AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2)
            )
        )
        self._addFilter(filterDict)
    
    def perspectiveTransform(self, topLeft: Point = (118.0, 484.0), topRight: Point = (646.0, 507.0), bottomRight: Point = (548.0, 140.0), bottomLeft: Point = (155.0, 153.0)):
        """
        Alters the geometry of an image to simulate the observer changing viewing position. You can use the perspective filter to skew an image.
        
        **Arguments:**
        
        `topLeft` a tuple (x, y). The top left coordinate to map the image to.
        `topRight` a tuple (x, y). The top right coordinate to map the image to.
        `bottomRight` a tuple (x, y). The bottom right coordinate to map the image to.
        `bottomLeft` a tuple (x, y). The bottom left coordinate to map the image to.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPerspectiveTransform',
            attributes=dict(
                topLeft=AppKit.CIVector.vectorWithValues_count_(topLeft, 2),
                topRight=AppKit.CIVector.vectorWithValues_count_(topRight, 2),
                bottomRight=AppKit.CIVector.vectorWithValues_count_(bottomRight, 2),
                bottomLeft=AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2)
            )
        )
        self._addFilter(filterDict)
    
    def perspectiveTransformWithExtent(self, extent: BoundingBox = (0.0, 0.0, 300.0, 300.0), topLeft: Point = (118.0, 484.0), topRight: Point = (646.0, 507.0), bottomRight: Point = (548.0, 140.0), bottomLeft: Point = (155.0, 153.0)):
        """
        Alters the geometry of an image to simulate the observer changing viewing position. You can use the perspective filter to skew an image.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `topLeft` a tuple (x, y). The top left coordinate to map the image to.
        `topRight` a tuple (x, y). The top right coordinate to map the image to.
        `bottomRight` a tuple (x, y). The bottom right coordinate to map the image to.
        `bottomLeft` a tuple (x, y). The bottom left coordinate to map the image to.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPerspectiveTransformWithExtent',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                topLeft=AppKit.CIVector.vectorWithValues_count_(topLeft, 2),
                topRight=AppKit.CIVector.vectorWithValues_count_(topRight, 2),
                bottomRight=AppKit.CIVector.vectorWithValues_count_(bottomRight, 2),
                bottomLeft=AppKit.CIVector.vectorWithValues_count_(bottomLeft, 2)
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectChrome(self, extrapolate: bool = False):
        """
        Apply a "Chrome" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectChrome',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectFade(self, extrapolate: bool = False):
        """
        Apply a "Fade" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectFade',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectInstant(self, extrapolate: bool = False):
        """
        Apply an "Instant" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectInstant',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectMono(self, extrapolate: bool = False):
        """
        Apply a "Mono" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectMono',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectNoir(self, extrapolate: bool = False):
        """
        Apply a "Noir" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectNoir',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectProcess(self, extrapolate: bool = False):
        """
        Apply a "Process" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectProcess',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectTonal(self, extrapolate: bool = False):
        """
        Apply a "Tonal" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectTonal',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def photoEffectTransfer(self, extrapolate: bool = False):
        """
        Apply a "Transfer" style effect to an image.
        
        **Arguments:**
        
        `extrapolate` a float. If true, then the color effect will be extrapolated if the input image contains RGB component values outside the range 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPhotoEffectTransfer',
            attributes=dict(
                extrapolate=extrapolate
            )
        )
        self._addFilter(filterDict)
    
    def pinchDistortion(self, center: Point = (150.0, 150.0), radius: float = 300.0, scale: float = 0.5):
        """
        Creates a rectangular-shaped area that pinches source pixels inward, distorting those pixels closest to the rectangle the most.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        `scale` a float. The amount of pinching. A value of 0.0 has no effect. A value of 1.0 is the maximum pinch.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPinchDistortion',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius,
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def pinLightBlendMode(self, backgroundImage: Self):
        """
        Unpremultiplies the source and background image sample color, combines them according to the relative difference, and then blends the result with the background according to the PDF basic compositing formula. Source image values that are brighter than the destination will produce an output that is lighter than the destination. Source image values that are darker than the destination will produce an output that is darker than the destination.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPinLightBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def pixellate(self, center: Point = (150.0, 150.0), scale: float = 8.0):
        """
        Makes an image blocky.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `scale` a float. The scale determines the size of the squares. Larger values result in larger squares.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPixellate',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def pointillize(self, radius: float = 20.0, center: Point = (150.0, 150.0)):
        """
        Renders the source image in a pointillistic style.
        
        **Arguments:**
        
        `radius` a float. The radius of the circles in the resulting pattern.
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIPointillize',
            attributes=dict(
                radius=radius,
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1])
            )
        )
        self._addFilter(filterDict)
    
    def QRCodeGenerator(self, size: Size, message: str, correctionLevel: str = 'M'):
        """
        Generate a QR Code image for message data.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `message` a string. The message to encode in the QR Code
        `correctionLevel` a string. QR Code correction level L, M, Q, or H.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIQRCodeGenerator',
            attributes=dict(
                message=AppKit.NSData.dataWithBytes_length_(message, len(message)),
                correctionLevel=correctionLevel
            ),
            size=size,
            isGenerator=True,
            fitImage=True
        ),
        self._addFilter(filterDict)
    
    def radialGradient(self, size: Size, center: Point = (150.0, 150.0), radius0: float = 5.0, radius1: float = 100.0, color0: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), color1: RGBAColorTuple = (0.0, 0.0, 0.0, 1.0)):
        """
        Generates a gradient that varies radially between two circles having the same center. It is valid for one of the two circles to have a radius of 0.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius0` a float. The radius of the starting circle to use in the gradient.
        `radius1` a float. The radius of the ending circle to use in the gradient.
        `color0` RGBA tuple Color (r, g, b, a). The first color to use in the gradient.
        `color1` RGBA tuple Color (r, g, b, a). The second color to use in the gradient.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIRadialGradient',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius0=radius0,
                radius1=radius1,
                color0=AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3]),
                color1=AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def randomGenerator(self, size: Size):
        """
        Generates an image of infinite extent whose pixel values are made up of four independent, uniformly-distributed random numbers in the 0 to 1 range.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIRandomGenerator',
            size=size,
            isGenerator=True
        )
        self._addFilter(filterDict)
    
    def rippleTransition(self, targetImage: Self, shadingImage: Self, center: Point = (150.0, 150.0), extent: BoundingBox = (0.0, 0.0, 300.0, 300.0), time: float = 0.0, width: float = 100.0, scale: float = 50.0):
        """
        Transitions from one image to another by creating a circular wave that expands from the center point, revealing the new image in the wake of the wave.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `shadingImage` an Image object. An image that looks like a shaded sphere enclosed in a square image.
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `width` a float. The width of the ripple.
        `scale` a float. A value that determines whether the ripple starts as a bulge (higher value) or a dimple (lower value).
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIRippleTransition',
            attributes=dict(
                targetImage=targetImage,
                shadingImage=shadingImage,
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                time=time,
                width=width,
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def roundedRectangleGenerator(self, size: Size, extent: BoundingBox = (0.0, 0.0, 100.0, 100.0), radius: float = 10.0, color: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0)):
        """
        Generates a rounded rectangle image with the specified extent, corner radius, and color.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `radius` a float. The distance from the center of the effect.
        `color` RGBA tuple Color (r, g, b, a). A color.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIRoundedRectangleGenerator',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                radius=radius,
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def roundedRectangleStrokeGenerator(self, size: Size, extent: BoundingBox = (0.0, 0.0, 100.0, 100.0), radius: float = 10.0, color: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), width: float = 10.0):
        """
        Generates a rounded rectangle stroke image with the specified extent, corner radius, stroke width, and color.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `extent` a tuple (x, y, w, h). A rectangle that defines the extent of the effect.
        `radius` a float. The distance from the center of the effect.
        `color` RGBA tuple Color (r, g, b, a). A color.
        `width` a float. The width in pixels of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIRoundedRectangleStrokeGenerator',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                radius=radius,
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                width=width
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def rowAverage(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0)):
        """
        Calculates the average color for each row of the specified area in an image, returning the result in a 1D image.
        
        **Arguments:**
        
        `extent` a tuple (x, y, w, h). A rectangle that specifies the subregion of the image that you want to process.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIRowAverage',
            attributes=dict(
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4)
            )
        )
        self._addFilter(filterDict)
    
    def saliencyMapFilter(self):
        """
        Generates output image as a saliency map of the input image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISaliencyMapFilter',
        )
        self._addFilter(filterDict)
    
    def sampleNearest(self):
        """
        Produces an image that forces the image sampling to "nearest" mode instead of the default "linear" mode. This filter can be used to alter the behavior of filters that alter the geometry of an image. The output of this filter should be passed as the input to the geometry filter. For example, passing the output of this filter to CIAffineTransform can be used to produce a pixelated upsampled image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISampleNearest',
        )
        self._addFilter(filterDict)
    
    def saturationBlendMode(self, backgroundImage: Self):
        """
        Uses the luminance and hue values of the background with the saturation of the source image. Areas of the background that have no saturation (that is, pure gray areas) do not produce a change.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISaturationBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def screenBlendMode(self, backgroundImage: Self):
        """
        Multiplies the inverse of the source image samples with the inverse of the background image samples. This results in colors that are at least as light as either of the two contributing sample colors.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIScreenBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def sepiaTone(self, intensity: float = 1.0):
        """
        Maps the colors of an image to various shades of brown.
        
        **Arguments:**
        
        `intensity` a float. The intensity of the sepia effect. A value of 1.0 creates a monochrome sepia image. A value of 0.0 has no effect on the image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISepiaTone',
            attributes=dict(
                intensity=intensity
            )
        )
        self._addFilter(filterDict)
    
    def shadedMaterial(self, shadingImage: Self, scale: float = 10.0):
        """
        Produces a shaded image from a height field. The height field is defined to have greater heights with lighter shades, and lesser heights (lower areas) with darker shades. You can combine this filter with the "Height Field From Mask" filter to produce quick shadings of masks, such as text.
        
        **Arguments:**
        
        `shadingImage` an Image object. The image to use as the height field. The resulting image has greater heights with lighter shades, and lesser heights (lower areas) with darker shades.
        `scale` a float. The scale of the effect. The higher the value, the more dramatic the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIShadedMaterial',
            attributes=dict(
                shadingImage=shadingImage,
                scale=scale
            )
        )
        self._addFilter(filterDict)
    
    def sharpenLuminance(self, sharpness: float = 0.4, radius: float = 1.69):
        """
        Increases image detail by sharpening. It operates on the luminance of the image; the chrominance of the pixels remains unaffected.
        
        **Arguments:**
        
        `sharpness` a float. The amount of sharpening to apply. Larger values are sharper.
        `radius` a float. The distance from the center of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISharpenLuminance',
            attributes=dict(
                sharpness=sharpness,
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def sixfoldReflectedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0):
        """
        Produces a tiled image from a source image by applying a 6-way reflected symmetry.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISixfoldReflectedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def sixfoldRotatedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0):
        """
        Produces a tiled image from a source image by rotating the source at increments of 60 degrees.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISixfoldRotatedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def smoothLinearGradient(self, size: Size, point0: Point = (0.0, 0.0), point1: Point = (200.0, 200.0), color0: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), color1: RGBAColorTuple = (0.0, 0.0, 0.0, 1.0)):
        """
        Generates a gradient that varies along a linear axis between two defined endpoints.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `point0` a tuple (x, y). The starting position of the gradient -- where the first color begins.
        `point1` a tuple (x, y). The ending position of the gradient -- where the second color begins.
        `color0` RGBA tuple Color (r, g, b, a). The first color to use in the gradient.
        `color1` RGBA tuple Color (r, g, b, a). The second color to use in the gradient.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISmoothLinearGradient',
            attributes=dict(
                point0=AppKit.CIVector.vectorWithValues_count_(point0, 2),
                point1=AppKit.CIVector.vectorWithValues_count_(point1, 2),
                color0=AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3]),
                color1=AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3])
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def sobelGradients(self):
        """
        Applies multichannel 3 by 3 Sobel gradient filter to an image. The resulting image has maximum horizontal gradient in the red channel and the maximum vertical gradient in the green channel. The gradient values can be positive or negative.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISobelGradients',
        )
        self._addFilter(filterDict)
    
    def softLightBlendMode(self, backgroundImage: Self):
        """
        Either darkens or lightens colors, depending on the source image sample color. If the source image sample color is lighter than 50% gray, the background is lightened, similar to dodging. If the source image sample color is darker than 50% gray, the background is darkened, similar to burning. If the source image sample color is equal to 50% gray, the background is not changed. Image samples that are equal to pure black or pure white produce darker or lighter areas, but do not result in pure black or white. The overall effect is similar to what you would achieve by shining a diffuse spotlight on the source image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISoftLightBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def sourceAtopCompositing(self, backgroundImage: Self):
        """
        Places the source image over the background image, then uses the luminance of the background image to determine what to show. The composite shows the background image and only those portions of the source image that are over visible parts of the background.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISourceAtopCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def sourceInCompositing(self, backgroundImage: Self):
        """
        Uses the second image to define what to leave in the source image, effectively cropping the image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISourceInCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def sourceOutCompositing(self, backgroundImage: Self):
        """
        Uses the second image to define what to take out of the first image.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISourceOutCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def sourceOverCompositing(self, backgroundImage: Self):
        """
        Places the second image over the first.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISourceOverCompositing',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def spotColor(self, centerColor1: RGBAColorTuple = (0.0784, 0.0627, 0.0706, 1.0), replacementColor1: RGBAColorTuple = (0.4392, 0.1922, 0.1961, 1.0), closeness1: float = 0.22, contrast1: float = 0.98, centerColor2: RGBAColorTuple = (0.5255, 0.3059, 0.3451, 1.0), replacementColor2: RGBAColorTuple = (0.9137, 0.5608, 0.5059, 1.0), closeness2: float = 0.15, contrast2: float = 0.98, centerColor3: RGBAColorTuple = (0.9216, 0.4549, 0.3333, 1.0), replacementColor3: RGBAColorTuple = (0.9098, 0.7529, 0.6078, 1.0), closeness3: float = 0.5, contrast3: float = 0.99):
        """
        Replaces one or more color ranges with spot colors.
        
        **Arguments:**
        
        `centerColor1` RGBA tuple Color (r, g, b, a). The center value of the first color range to replace.
        `replacementColor1` RGBA tuple Color (r, g, b, a). A replacement color for the first color range.
        `closeness1` a float. A value that indicates how close the first color must match before it is replaced.
        `contrast1` a float. The contrast of the first replacement color.
        `centerColor2` RGBA tuple Color (r, g, b, a). The center value of the second color range to replace.
        `replacementColor2` RGBA tuple Color (r, g, b, a). A replacement color for the second color range.
        `closeness2` a float. A value that indicates how close the second color must match before it is replaced.
        `contrast2` a float. The contrast of the second replacement color.
        `centerColor3` RGBA tuple Color (r, g, b, a). The center value of the third color range to replace.
        `replacementColor3` RGBA tuple Color (r, g, b, a). A replacement color for the third color range.
        `closeness3` a float. A value that indicates how close the third color must match before it is replaced.
        `contrast3` a float. The contrast of the third replacement color.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISpotColor',
            attributes=dict(
                centerColor1=AppKit.CIColor.colorWithRed_green_blue_alpha_(centerColor1[0], centerColor1[1], centerColor1[2], centerColor1[3]),
                replacementColor1=AppKit.CIColor.colorWithRed_green_blue_alpha_(replacementColor1[0], replacementColor1[1], replacementColor1[2], replacementColor1[3]),
                closeness1=closeness1,
                contrast1=contrast1,
                centerColor2=AppKit.CIColor.colorWithRed_green_blue_alpha_(centerColor2[0], centerColor2[1], centerColor2[2], centerColor2[3]),
                replacementColor2=AppKit.CIColor.colorWithRed_green_blue_alpha_(replacementColor2[0], replacementColor2[1], replacementColor2[2], replacementColor2[3]),
                closeness2=closeness2,
                contrast2=contrast2,
                centerColor3=AppKit.CIColor.colorWithRed_green_blue_alpha_(centerColor3[0], centerColor3[1], centerColor3[2], centerColor3[3]),
                replacementColor3=AppKit.CIColor.colorWithRed_green_blue_alpha_(replacementColor3[0], replacementColor3[1], replacementColor3[2], replacementColor3[3]),
                closeness3=closeness3,
                contrast3=contrast3
            )
        )
        self._addFilter(filterDict)
    
    def spotLight(self, lightPosition: tuple = (400.0, 600.0, 150.0), lightPointsAt: tuple = (200.0, 200.0, 0.0), brightness: float = 3.0, concentration: float = 0.1, color: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0)):
        """
        Applies a directional spotlight effect to an image.
        
        **Arguments:**
        
        `lightPosition` a tulple (x, y, z). The x and y position of the spotlight.
        `lightPointsAt` a tuple (x, y). The x and y position that the spotlight points at.
        `brightness` a float. The brightness of the spotlight.
        `concentration` a float. The spotlight size. The smaller the value, the more tightly focused the light beam.
        `color` RGBA tuple Color (r, g, b, a). The color of the spotlight.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISpotLight',
            attributes=dict(
                lightPosition=AppKit.CIVector.vectorWithValues_count_(lightPosition, 3),
                lightPointsAt=AppKit.CIVector.vectorWithValues_count_(lightPointsAt, 2),
                brightness=brightness,
                concentration=concentration,
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
            )
        )
        self._addFilter(filterDict)
    
    def SRGBToneCurveToLinear(self):
        """
        Converts an image in sRGB space to linear space.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISRGBToneCurveToLinear',
        )
        self._addFilter(filterDict)
    
    def starShineGenerator(self, size: Size, center: Point = (150.0, 150.0), color: RGBAColorTuple = (1.0, 0.8, 0.6, 1.0), radius: float = 50.0, crossScale: float = 15.0, crossAngle: float = 0.6, crossOpacity: float = -2.0, crossWidth: float = 2.5, epsilon: float = -2.0):
        """
        Generates a starburst pattern. The output image is typically used as input to another filter.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `color` RGBA tuple Color (r, g, b, a). The color to use for the outer shell of the circular star.
        `radius` a float. The radius of the star.
        `crossScale` a float. The size of the cross pattern.
        `crossAngle` a float in degrees. The angle in degrees of the cross pattern.
        `crossOpacity` a float. The opacity of the cross pattern.
        `crossWidth` a float. The width of the cross pattern.
        `epsilon` a float. The length of the cross spikes.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIStarShineGenerator',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                radius=radius,
                crossScale=crossScale,
                crossAngle=radians(crossAngle),
                crossOpacity=crossOpacity,
                crossWidth=crossWidth,
                epsilon=epsilon
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def straightenFilter(self, angle: float = 0.0):
        """
        Rotates a source image by the specified angle in radians. The image is then scaled and cropped so that the rotated image fits the extent of the input image.
        
        **Arguments:**
        
        `angle` a float in degrees. The angle in degrees of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIStraightenFilter',
            attributes=dict(
                angle=radians(angle)
            )
        )
        self._addFilter(filterDict)
    
    def stretchCrop(self, size: Point = (1280.0, 720.0), cropAmount: float = 0.25, centerStretchAmount: float = 0.25):
        """
        Distorts an image by stretching and or cropping to fit a target size.
        
        **Arguments:**
        
        `size` a tuple (w, h). The size in pixels of the output image.
        `cropAmount` a float. Determines if and how much cropping should be used to achieve the target size. If value is 0 then only stretching is used. If 1 then only cropping is used.
        `centerStretchAmount` a float. Determine how much the center of the image is stretched if stretching is used. If value is 0 then the center of the image maintains the original aspect ratio. If 1 then the image is stretched uniformly.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIStretchCrop',
            attributes=dict(
                size=size,
                cropAmount=cropAmount,
                centerStretchAmount=centerStretchAmount
            )
        )
        self._addFilter(filterDict)
    
    def stripesGenerator(self, size: Size, center: Point = (150.0, 150.0), color0: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), color1: RGBAColorTuple = (0.0, 0.0, 0.0, 1.0), width: float = 80.0, sharpness: float = 1.0):
        """
        Generates a stripe pattern. You can control the color of the stripes, the spacing, and the contrast.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `color0` RGBA tuple Color (r, g, b, a). A color to use for the odd stripes.
        `color1` RGBA tuple Color (r, g, b, a). A color to use for the even stripes.
        `width` a float. The width of a stripe.
        `sharpness` a float. The sharpness of the stripe pattern. The smaller the value, the more blurry the pattern. Values range from 0.0 to 1.0.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIStripesGenerator',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                color0=AppKit.CIColor.colorWithRed_green_blue_alpha_(color0[0], color0[1], color0[2], color0[3]),
                color1=AppKit.CIColor.colorWithRed_green_blue_alpha_(color1[0], color1[1], color1[2], color1[3]),
                width=width,
                sharpness=sharpness
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def subtractBlendMode(self, backgroundImage: Self):
        """
        Unpremultiplies the source and background image sample colors, subtracts the source from the background, and then blends the result with the background according to the PDF basic compositing formula. Source image values that are black produces output that is the same as the background. Source image values that are non-black darken the background color values.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISubtractBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def sunbeamsGenerator(self, size: Size, center: Point = (150.0, 150.0), color: RGBAColorTuple = (1.0, 0.5, 0.0, 1.0), sunRadius: float = 40.0, maxStriationRadius: float = 2.58, striationStrength: float = 0.5, striationContrast: float = 1.375, time: float = 0.0):
        """
        Generates a sun effect. You typically use the output of the sunbeams filter as input to a composite filter.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `color` RGBA tuple Color (r, g, b, a). The color of the sun.
        `sunRadius` a float. The radius of the sun.
        `maxStriationRadius` a float. The radius of the sunbeams.
        `striationStrength` a float. The intensity of the sunbeams. Higher values result in more intensity.
        `striationContrast` a float. The contrast of the sunbeams. Higher values result in more contrast.
        `time` a float. The duration of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISunbeamsGenerator',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                sunRadius=sunRadius,
                maxStriationRadius=maxStriationRadius,
                striationStrength=striationStrength,
                striationContrast=striationContrast,
                time=time
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def swipeTransition(self, targetImage: Self, extent: BoundingBox = (0.0, 0.0, 300.0, 300.0), color: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0), time: float = 0.0, angle: float = 0.0, width: float = 300.0, opacity: float = 0.0):
        """
        Transitions from one image to another by simulating a swiping action.
        
        **Arguments:**
        
        `targetImage` an Image object. The target image for a transition.
        `extent` a tuple (x, y, w, h). The extent of the effect.
        `color` RGBA tuple Color (r, g, b, a). The color of the swipe.
        `time` a float. The parametric time of the transition. This value drives the transition from start (at time 0) to end (at time 1).
        `angle` a float in degrees. The angle in degrees of the swipe.
        `width` a float. The width of the swipe.
        `opacity` a float. The opacity of the swipe.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CISwipeTransition',
            attributes=dict(
                targetImage=targetImage,
                extent=AppKit.CIVector.vectorWithValues_count_(extent, 4),
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]),
                time=time,
                angle=radians(angle),
                width=width,
                opacity=opacity
            )
        )
        self._addFilter(filterDict)
    
    def temperatureAndTint(self, neutral: Point = (6500.0, 0.0), targetNeutral: Point = (6500.0, 0.0)):
        """
        Adapt the reference white point for an image.
        
        **Arguments:**
        
        `neutral` a tuple. A vector containing the source white point defined by color temperature and tint or chromaticity (x,y).
        `targetNeutral` a tuple. A vector containing the desired white point defined by color temperature and tint or chromaticity (x,y).
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CITemperatureAndTint',
            attributes=dict(
                neutral=AppKit.CIVector.vectorWithValues_count_(neutral, 2),
                targetNeutral=AppKit.CIVector.vectorWithValues_count_(targetNeutral, 2)
            )
        )
        self._addFilter(filterDict)
    
    def textImageGenerator(self, size: Size, text: FormattedString, fontName: str = 'HelveticaNeue', fontSize: float = 12.0, scaleFactor: float = 1.0, padding: float = 0.0):
        """
        Generate an image from a string and font information.
        
        **Arguments:**
        
        `size` a tuple (w, h)
        `text` a `FormattedString`. The text to render.
        `fontName` a float. The name of the font to use for the generated text.
        `fontSize` a float. The size of the font to use for the generated text.
        `scaleFactor` a float. The scale of the font to use for the generated text.
        `padding` a float. The number of additional pixels to pad around the text’s bounding box.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CITextImageGenerator',
            attributes=dict(
                text=text.getNSObject(),
                fontName=fontName,
                fontSize=fontSize,
                scaleFactor=scaleFactor,
                padding=padding
            ),
            size=size,
            isGenerator=True
        ),
        self._addFilter(filterDict)
    
    def thermal(self):
        """
        Apply a "Thermal" style effect to an image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIThermal',
        )
        self._addFilter(filterDict)
    
    def toneCurve(self, point0: Point = (0.0, 0.0), point1: Point = (0.25, 0.25), point2: Point = (0.5, 0.5), point3: Point = (0.75, 0.75), point4: Point = (1.0, 1.0)):
        """
        Adjusts tone response of the R, G, and B channels of an image. The input points are five x,y values that are interpolated using a spline curve. The curve is applied in a perceptual (gamma 2) version of the working space.
        
        **Arguments:**
        
        `point0` a tuple (x, y). 
        `point1` a tuple (x, y). 
        `point2` a tuple (x, y). 
        `point3` a tuple (x, y). 
        `point4` a tuple (x, y). 
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIToneCurve',
            attributes=dict(
                point0=AppKit.CIVector.vectorWithValues_count_(point0, 2),
                point1=AppKit.CIVector.vectorWithValues_count_(point1, 2),
                point2=AppKit.CIVector.vectorWithValues_count_(point2, 2),
                point3=AppKit.CIVector.vectorWithValues_count_(point3, 2),
                point4=AppKit.CIVector.vectorWithValues_count_(point4, 2)
            )
        )
        self._addFilter(filterDict)
    
    def torusLensDistortion(self, center: Point = (150.0, 150.0), radius: float = 160.0, width: float = 80.0, refraction: float = 1.7):
        """
        Creates a torus-shaped lens and distorts the portion of the image over which the lens is placed.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The outer radius of the torus.
        `width` a float. The width of the ring.
        `refraction` a float. The refraction of the glass.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CITorusLensDistortion',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius,
                width=width,
                refraction=refraction
            )
        )
        self._addFilter(filterDict)
    
    def triangleKaleidoscope(self, point: Point = (150.0, 150.0), size: float = 700.0, rotation: float = 5.924285296593801, decay: float = 0.85):
        """
        Maps a triangular portion of image to a triangular area and then generates a kaleidoscope effect.
        
        **Arguments:**
        
        `point` a tuple (x, y). The x and y position to use as the center of the triangular area in the input image.
        `size` a tuple (w, h). The size in pixels of the triangle.
        `rotation` a float. Rotation angle in degrees of the triangle.
        `decay` a float. The decay determines how fast the color fades from the center triangle.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CITriangleKaleidoscope',
            attributes=dict(
                point=AppKit.CIVector.vectorWithValues_count_(point, 2),
                size=size,
                rotation=rotation,
                decay=decay
            )
        )
        self._addFilter(filterDict)
    
    def triangleTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0):
        """
        Maps a triangular portion of image to a triangular area and then tiles the result.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CITriangleTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def twelvefoldReflectedTile(self, center: Point = (150.0, 150.0), angle: float = 0.0, width: float = 100.0):
        """
        Produces a tiled image from a source image by applying a 12-way reflected symmetry.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `angle` a float in degrees. The angle in degrees of the tiled pattern.
        `width` a float. The width of a tile.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CITwelvefoldReflectedTile',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                angle=radians(angle),
                width=width
            )
        )
        self._addFilter(filterDict)
    
    def twirlDistortion(self, center: Point = (150.0, 150.0), radius: float = 300.0, angle: float = 3.141592653589793):
        """
        Rotates pixels around a point to give a twirling effect. You can specify the number of rotations as well as the center and radius of the effect.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        `angle` a float in degrees. The angle in degrees of the twirl. Values can be positive or negative.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CITwirlDistortion',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius,
                angle=radians(angle)
            )
        )
        self._addFilter(filterDict)
    
    def unsharpMask(self, radius: float = 2.5, intensity: float = 0.5):
        """
        Increases the contrast of the edges between pixels of different colors in an image.
        
        **Arguments:**
        
        `radius` a float. The radius around a given pixel to apply the unsharp mask. The larger the radius, the more of the image is affected.
        `intensity` a float. The intensity of the effect. The larger the value, the more contrast in the affected area.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIUnsharpMask',
            attributes=dict(
                radius=radius,
                intensity=intensity
            )
        )
        self._addFilter(filterDict)
    
    def vibrance(self, amount: float = 0.0):
        """
        Adjusts the saturation of an image while keeping pleasing skin tones.
        
        **Arguments:**
        
        `amount` a float. The amount to adjust the saturation.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIVibrance',
            attributes=dict(
                amount=amount
            )
        )
        self._addFilter(filterDict)
    
    def vignette(self, intensity: float = 0.0, radius: float = 1.0):
        """
        Applies a vignette shading to the corners of an image.
        
        **Arguments:**
        
        `intensity` a float. The intensity of the effect.
        `radius` a float. The distance from the center of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIVignette',
            attributes=dict(
                intensity=intensity,
                radius=radius
            )
        )
        self._addFilter(filterDict)
    
    def vignetteEffect(self, center: Point = (150.0, 150.0), radius: float = 150.0, intensity: float = 1.0, falloff: float = 0.5):
        """
        Applies a vignette shading to the corners of an image.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The distance from the center of the effect.
        `intensity` a float. The intensity of the effect.
        `falloff` a float. The falloff of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIVignetteEffect',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                radius=radius,
                intensity=intensity,
                falloff=falloff
            )
        )
        self._addFilter(filterDict)
    
    def vividLightBlendMode(self, backgroundImage: Self):
        """
        A blend mode that is a combination of color burn and color dodge blend modes.
        
        **Arguments:**
        
        `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIVividLightBlendMode',
            attributes=dict(
                backgroundImage=backgroundImage
            )
        )
        self._addFilter(filterDict)
    
    def vortexDistortion(self, center: Point = (150.0, 150.0), radius: float = 300.0, angle: float = 56.548667764616276):
        """
        Rotates pixels around a point to simulate a vortex. You can specify the number of rotations as well the center and radius of the effect. 
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `radius` a float. The radius determines how many pixels are used to create the distortion. The larger the radius, the wider the extent of the distortion.
        `angle` a float in degrees. The angle in degrees of the effect.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIVortexDistortion',
            attributes=dict(
                center=center,
                radius=radius,
                angle=angle
            )
        )
        self._addFilter(filterDict)
    
    def whitePointAdjust(self, color: RGBAColorTuple = (1.0, 1.0, 1.0, 1.0)):
        """
        Adjusts the reference white point for an image and maps all colors in the source using the new reference.
        
        **Arguments:**
        
        `color` RGBA tuple Color (r, g, b, a). A color to use as the white point.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIWhitePointAdjust',
            attributes=dict(
                color=AppKit.CIColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3])
            )
        )
        self._addFilter(filterDict)
    
    def XRay(self):
        """
        Apply an "XRay" style effect to an image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIXRay',
        )
        self._addFilter(filterDict)
    
    def zoomBlur(self, center: Point = (150.0, 150.0), amount: float = 20.0):
        """
        Simulates the effect of zooming the camera while capturing the image.
        
        **Arguments:**
        
        `center` a tuple (x, y). The center of the effect as x and y pixel coordinates.
        `amount` a float. The zoom-in amount. Larger values result in more zooming in.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        filterDict = dict(
            name='CIZoomBlur',
            attributes=dict(
                center=AppKit.CIVector.vectorWithX_Y_(center[0], center[1]),
                amount=amount
            )
        )
        self._addFilter(filterDict)
    