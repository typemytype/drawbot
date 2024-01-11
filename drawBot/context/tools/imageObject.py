from typing import Any
import AppKit
from math import radians
import os

from drawBot.misc import DrawBotError, optimizePath
from drawBot.context.imageContext import _makeBitmapImageRep

from aliases import Point, SomePath, Transform, BoundingBox, Size
from typing_extensions import Self

from drawBot.context.baseContext import FormattedString


class ImageObject:

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
        if isinstance(path, AppKit.NSImage): # type: ignore
            im = path
        elif isinstance(path, (str, os.PathLike)):
            path = optimizePath(path)
            if path.startswith("http"):
                url = AppKit.NSURL.URLWithString_(path) # type: ignore
            else:
                if not os.path.exists(path):
                    raise DrawBotError("Image path '%s' does not exists." % path)
                url = AppKit.NSURL.fileURLWithPath_(path) # type: ignore
            im = AppKit.NSImage.alloc().initByReferencingURL_(url) # type: ignore
        else:
            raise DrawBotError("Cannot read image path '%s'." % path)
        rep = _makeBitmapImageRep(im)
        ciImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep) # type: ignore
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
        im = AppKit.NSImage.alloc().initWithData_(page.dataRepresentation()) # type: ignore
        # create an CIImage object
        rep = _makeBitmapImageRep(im)
        ciImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep) # type: ignore
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
        rep = AppKit.NSCIImageRep.imageRepWithCIImage_(self._ciImage()) # type: ignore
        nsImage = AppKit.NSImage.alloc().initWithSize_(rep.size()) # type: ignore
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

    def _addFilter(self, filterDict: dict[str, Any]):
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
            ciFilter = AppKit.CIFilter.filterWithName_(filterName) # type: ignore
            ciFilter.setDefaults()

            for key, value in filterDict.get("attributes", {}).items():
                ciFilter.setValue_forKey_(value, key)

            if filterDict.get("isGenerator", False):
                generator = ciFilter.valueForKey_("outputImage")
                extent = generator.extent()
                w, h = filterDict.get("size", extent.size)
                dummy = AppKit.NSImage.alloc().initWithSize_((w, h)) # type: ignore

                scaleX = w / extent.size.width
                scaleY = h / extent.size.height
                dummy.lockFocus()
                ctx = AppKit.NSGraphicsContext.currentContext() # type: ignore
                ctx.setShouldAntialias_(False)
                ctx.setImageInterpolation_(AppKit.NSImageInterpolationNone) # type: ignore
                fromRect = (0, 0), (w, h)
                if filterDict.get("fitImage", False):
                    transform = AppKit.NSAffineTransform.transform() # type: ignore
                    transform.scaleXBy_yBy_(scaleX, scaleY)
                    transform.concat()
                    fromRect = extent
                generator.drawAtPoint_fromRect_operation_fraction_((0, 0), fromRect, AppKit.NSCompositeCopy, 1) # type: ignore
                dummy.unlockFocus()
                rep = _makeBitmapImageRep(dummy)
                self._cachedImage = AppKit.CIImage.alloc().initWithBitmapImageRep_(rep) # type: ignore # type: ignore
                del dummy
            elif hasattr(self, "_cachedImage"):
                ciFilter.setValue_forKey_(self._cachedImage, "inputImage")
                self._cachedImage = ciFilter.valueForKey_("outputImage")
        if not hasattr(self, "_cachedImage"):
            raise DrawBotError("Image does not contain any data. Draw into the image object first or set image data from a path.")

    # --- filters ---
    # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
    # please, do not attempt to edit it manually as it will be overriden in the future
    
    def accordionFoldTransition(self, targetImage: Self, bottomHeight: float = 0.0, numberOfFolds: float = 3, foldShadowAmount: float = 0.1, time: float = 0.0):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Transitions from one image to another of a differing dimensions by unfolding.
        
        Attributes:
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
                targetImage=targetImage._ciImage(),
                bottomHeight=bottomHeight,
                numberOfFolds=numberOfFolds,
                foldShadowAmount=foldShadowAmount,
                time=time
            )
        )
        self._addFilter(filterDict)
    
    def additionCompositing(self, backgroundImage: Self):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Adds color components to achieve a brightening effect. This filter is typically used to add highlights and lens flare effects.
        
        Attributes:
            `backgroundImage` an Image object. The image to use as a background image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        filterDict = dict(
            name='CIAdditionCompositing',
            attributes=dict(
                backgroundImage=backgroundImage._ciImage()
            )
        )
        self._addFilter(filterDict)
    
    def affineClamp(self, transform: Transform = (0.4, 0.0, 0.0, 0.4, 0.0, 0.0)):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Performs an affine transformation on a source image and then clamps the pixels at the edge of the transformed image, extending them outwards. This filter performs similarly to the “Affine Transform” filter except that it produces an image with infinite extent. You can use this filter when you need to blur an image but you want to avoid a soft, black fringe along the edges.
        
        Attributes:
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
    
    def affineTile(self, transform: Transform = (0.4, 0.0, 0.0, 0.4, 0.0, 0.0)):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Applies an affine transformation to an image and then tiles the transformed image.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Calculates the average color for the specified area in an image, returning the result in a pixel.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Calculates histograms of the R, G, B, and A channels of the specified area of an image. The output image is a one pixel tall image containing the histogram data for all four channels.
        
        Attributes:
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
    
    def areaLogarithmicHistogram(self, extent: BoundingBox = (0.0, 0.0, 640.0, 80.0), scale: float = 1.0, count: float = 64.0, minimumStop: float = -10, maximumStop: float = 4):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Calculates histogram of the R, G, B, and A channels of the specified area of an image. Before binning, the R, G, and B channel values are transformed by the log base two function. The output image is a one pixel tall image containing the histogram data for all four channels.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Calculates the maximum component values for the specified area in an image, returning the result in a pixel.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Finds and returns the pixel with the maximum alpha value.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Calculates the minimum component values for the specified area in an image, returning the result in a pixel.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Finds and returns the pixel with the minimum alpha value.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Calculates the per-component minimum and maximum value for the specified area in an image. The result is returned in a 2x1 image where the component minimum values are stored in the pixel on the left.
        
        Attributes:
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
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Calculates the minimum and maximum red component value for the specified area in an image. The result is returned in the red and green channels of a one pixel image.
        
        Attributes:
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
    
    def attributedTextImageGenerator(self, size: Size, text: FormattedString, scaleFactor: float = 1, padding: float = 0):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Generate an image attributed string.
        
        Attributes:
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
    
    def aztecCodeGenerator(self, size: Size, message: str, correctionLevel: float = 23, layers: float | None = None, compactStyle: float | None = None):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Generate an Aztec barcode image for message data.
        
        Attributes:
            `size` a tuple (w, h)
            `message` a string. The message to encode in the Aztec Barcode
            `correctionLevel` a float. Aztec error correction value between 5 and 95
            `layers` a float. Aztec layers value between 1 and 32. Set to `None` for automatic.
            `compactStyle` a bool. Force a compact style Aztec code to `True` or `False`. Set to `None` for automatic.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        filterDict = dict(
            name='CIAztecCodeGenerator',
            attributes=dict(
                message=AppKit.NSData.dataWithBytes_length_(message, len(message)),
                correctionLevel=correctionLevel,
                layers=layers,
                compactStyle=compactStyle
            ),
            size=size,
            isGenerator=True,
            fitImage=True
        ),
        self._addFilter(filterDict)
    
    def barsSwipeTransition(self, targetImage: Self, angle: float = 3.141592653589793, width: float = 30.0, barOffset: float = 10.0, time: float = 0.0):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Transitions from one image to another by swiping rectangular portions of the foreground image to disclose the target image.
        
        Attributes:
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
                targetImage=targetImage._ciImage(),
                angle=radians(angle),
                width=width,
                barOffset=barOffset,
                time=time
            )
        )
        self._addFilter(filterDict)
    
    def blendWithAlphaMask(self, backgroundImage: Self, maskImage: Self):
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        Uses values from a mask image to interpolate between an image and the background. When a mask alpha value is 0.0, the result is the background. When the mask alpha value is 1.0, the result is the image.
        
        Attributes:
            `backgroundImage` an Image object. The image to use as a background image.
            `maskImage` an Image object. A masking image.
        """
        # the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`
        # please, do not attempt to edit it manually as it will be overriden in the future
        
        filterDict = dict(
            name='CIBlendWithAlphaMask',
            attributes=dict(
                backgroundImage=backgroundImage._ciImage(),
                maskImage=maskImage._ciImage()
            )
        )
        self._addFilter(filterDict)
    