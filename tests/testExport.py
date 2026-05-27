import glob
import io
import os
import random
import sys
import unittest

import AppKit  # type: ignore
import PIL
from PIL import ImageCms
from testSupport import (
    DrawBotBaseTest,
    StdOutCollector,
    TempFile,
    TempFolder,
    randomSeed,
    readData,
    tempTestDataDir,
    testDataDir,
)

import drawBot
from drawBot.context.tools.gifTools import gifFrameCount
from drawBot.misc import DrawBotError


class ExportTest(DrawBotBaseTest):
    def makeTestAnimation(self, numFrames=25, pageWidth=500, pageHeight=500):
        randomSeed(0)
        drawBot.newDrawing()
        for i in range(numFrames):
            drawBot.newPage(pageWidth, pageHeight)
            drawBot.frameDuration(1 / 25)
            drawBot.fill(1)
            drawBot.rect(0, 0, pageWidth, pageHeight)
            drawBot.fill(0)
            drawBot.rect(random.randint(0, 100), random.randint(0, 100), 400, 400)

    def makeTestDrawing(self):
        drawBot.newDrawing()
        drawBot.newPage(500, 500)
        drawBot.oval(100, 100, 300, 300)

    def _saveImageAndReturnSize(self, extension, **options):
        with TempFile(suffix=extension) as tmp:
            drawBot.saveImage(tmp.path, **options)
            fileSize = os.stat(tmp.path).st_size
        return fileSize

    def test_with_drawing(self):
        drawBot.newDrawing()
        self.assertEqual(drawBot.pageCount(), 0)
        with drawBot.drawing():
            for i in range(10):
                drawBot.newPage()
                drawBot.rect(10, 10, 10, 10)
            self.assertEqual(drawBot.pageCount(), 10)
        self.assertEqual(drawBot.pageCount(), 0)

    def test_ffmpegCodec(self):
        self.makeTestAnimation()
        size_h264 = self._saveImageAndReturnSize(".mp4")
        size_mpeg4 = self._saveImageAndReturnSize(".mp4", ffmpegCodec="mpeg4")
        self.assertLess(size_h264, size_mpeg4, "encoded with h264 is expected to be smaller than with mpeg4")

    def test_arbitraryOption(self):
        self.makeTestAnimation(1)
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".png", someArbitraryOption="foo")
        self.assertEqual(
            output.lines(),
            ["*** DrawBot warning: Unrecognized saveImage() option found for PNGContext: someArbitraryOption ***"],
        )

    def test_export_gif(self):
        self.makeTestAnimation(5)
        self._saveImageAndReturnSize(".gif")

    def test_export_png(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".png")

    def test_export_jpg(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".jpg")

    def test_export_jpeg(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".jpeg")

    def test_export_tif(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".tif")

    def test_export_tiff(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".tiff")

    def test_export_bmp(self):
        self.makeTestDrawing()
        self._saveImageAndReturnSize(".bmp")

    def test_export_pathlib(self):
        import pathlib

        self.makeTestDrawing()
        with TempFile(suffix=".png") as tmp:
            drawBot.saveImage(pathlib.Path(tmp.path))

    def test_imageResolution(self):
        self.makeTestDrawing()
        with TempFile(suffix=".png") as tmp:
            drawBot.saveImage(tmp.path)
            self.assertEqual(drawBot.imageSize(tmp.path), (500, 500))
            drawBot.saveImage(tmp.path, imageResolution=144)
            self.assertEqual(drawBot.imageSize(tmp.path), (1000, 1000))
            drawBot.saveImage(tmp.path, imageResolution=36)
            self.assertEqual(drawBot.imageSize(tmp.path), (250, 250))
            drawBot.saveImage(tmp.path, imageResolution=18)
            self.assertEqual(drawBot.imageSize(tmp.path), (125, 125))

    def test_imagePNGInterlaced(self):
        self.makeTestDrawing()
        defaultSize = self._saveImageAndReturnSize(".png")
        interlacedSize = self._saveImageAndReturnSize(".png", imagePNGInterlaced=True)
        # XXX Huh, seems to make no difference, output files are identical
        self.assertEqual(defaultSize, interlacedSize)

    def test_imagePNGGamma(self):
        self.makeTestDrawing()
        defaultSize = self._saveImageAndReturnSize(".png")
        gammaSize = self._saveImageAndReturnSize(".png", imagePNGGamma=0.8)
        self.assertLess(defaultSize, gammaSize)

    def test_imageJPEGProgressive(self):
        self.makeTestDrawing()
        defaultSize = self._saveImageAndReturnSize(".jpg")
        progressiveSize = self._saveImageAndReturnSize(".jpg", imageJPEGProgressive=True)
        self.assertGreater(defaultSize, progressiveSize)

    def test_imageJPEGCompressionFactor(self):
        self.makeTestDrawing()
        lowCompressionSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=1.0)
        mediumCompressionSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=0.5)
        highCompressionSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=0.0)
        self.assertGreater(lowCompressionSize, mediumCompressionSize)
        self.assertGreater(mediumCompressionSize, highCompressionSize)

    def test_imageTIFFCompressionMethod(self):
        self.makeTestDrawing()
        defaultCompressionSize = self._saveImageAndReturnSize(".tif")
        noCompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod=None)
        packbitsCompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod="packbits")
        packbits2CompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod=32773)
        packbits3CompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod="PACKBITS")
        lzwCompressionSize = self._saveImageAndReturnSize(".tif", imageTIFFCompressionMethod="lzw")
        self.assertEqual(defaultCompressionSize, noCompressionSize)
        self.assertEqual(packbitsCompressionSize, packbits2CompressionSize)
        self.assertEqual(packbitsCompressionSize, packbits3CompressionSize)
        self.assertGreater(noCompressionSize, packbitsCompressionSize)
        self.assertGreater(packbitsCompressionSize, lzwCompressionSize)

    def test_imageFallbackBackgroundColor(self):
        self.makeTestDrawing()
        with TempFile(suffix=".jpg") as tmp:
            drawBot.saveImage(tmp.path, imageJPEGCompressionFactor=1.0)
            self.assertEqual(drawBot.imagePixelColor(tmp.path, (5, 5)), (1.0, 1.0, 1.0, 1.0))
        with TempFile(suffix=".jpg") as tmp:
            drawBot.saveImage(tmp.path, imageJPEGCompressionFactor=1.0, imageFallbackBackgroundColor=(0, 1, 0))
            r, g, b, a = drawBot.imagePixelColor(tmp.path, (5, 5))
            self.assertEqual((round(r, 2), round(g, 2), round(b, 2)), (0, 1.0, 0))
        with TempFile(suffix=".jpg") as tmp:
            drawBot.saveImage(
                tmp.path, imageJPEGCompressionFactor=1.0, imageFallbackBackgroundColor=AppKit.NSColor.redColor()
            )
            r, g, b, a = drawBot.imagePixelColor(tmp.path, (5, 5))
            # TODO: fix excessive rounding. 2 digits fails on 10.13, at least on Travis
            self.assertEqual((round(r, 1), round(g, 1), round(b, 1)), (1, 0.0, 0))

    def test_imageAntiAliasing(self):
        expectedPath = os.path.join(testDataDir, "expected_imageAntiAliasing.png")

        drawBot.newDrawing()
        drawBot.size(100, 100)
        drawBot.fill(1, 0, 0)
        drawBot.oval(10, 10, 40, 80)
        drawBot.fill(0)
        drawBot.stroke(0)
        drawBot.line((-0.5, -0.5), (100.5, 100.5))
        drawBot.line((0, 20.5), (100, 20.5))
        drawBot.fontSize(20)
        drawBot.text("a", (62, 30))

        with TempFile(suffix=".png") as tmp:
            drawBot.saveImage(tmp.path, antiAliasing=False)
            self.assertImageFilesEqual(tmp.path, expectedPath)

    def test_imageFontSubpixelQuantization(self):
        expectedPath = os.path.join(testDataDir, "expected_imageFontSubpixelQuantization.png")

        drawBot.newDrawing()
        drawBot.size(30, 30)
        drawBot.fontSize(10)
        drawBot.font("Skia")
        drawBot.fontVariations(wght=0.789)
        drawBot.text("abc\nxyz", (6, 18))

        with TempFile(suffix=".png") as tmp:
            drawBot.saveImage(tmp.path, fontSubpixelQuantization=False)
            self.assertImageFilesEqual(tmp.path, expectedPath)

    def _testMultipage(self, extension, numFrames, expectedMultipageCount):
        self.makeTestAnimation(numFrames)
        with TempFolder() as tmpFolder:
            with TempFile(suffix=extension, dir=tmpFolder.path) as tmp:
                base, ext = os.path.splitext(tmp.path)
                pattern = base + "_*" + ext
                self.assertEqual(len(glob.glob(pattern)), 0)
                drawBot.saveImage(tmp.path)
                self.assertEqual(len(glob.glob(pattern)), 0)
                drawBot.saveImage(tmp.path, multipage=False)
                self.assertEqual(len(glob.glob(pattern)), 0)
                drawBot.saveImage(tmp.path, multipage=True)
                self.assertEqual(len(glob.glob(pattern)), expectedMultipageCount)
        assert not os.path.exists(tmpFolder.path)  # verify TempFolder cleanup

    def test_multipage_png(self):
        self._testMultipage(".png", numFrames=5, expectedMultipageCount=5)

    def test_multipage_jpg(self):
        self._testMultipage(".jpg", numFrames=6, expectedMultipageCount=6)

    def test_multipage_svg(self):
        self._testMultipage(".svg", numFrames=7, expectedMultipageCount=7)

    def test_multipage_gif(self):
        self._testMultipage(".gif", numFrames=8, expectedMultipageCount=0)

    def test_multipage_pdf(self):
        self._testMultipage(".pdf", numFrames=9, expectedMultipageCount=0)

    def test_animatedGIF(self):
        self.makeTestAnimation(5)
        with TempFile(suffix=".gif") as tmp:
            drawBot.saveImage(tmp.path)
            self.assertEqual(gifFrameCount(tmp.path), 5)

    def test_saveImage_unknownContext(self):
        self.makeTestDrawing()
        with self.assertRaises(DrawBotError) as cm:
            drawBot.saveImage("foo.abcde")
        self.assertEqual(cm.exception.args[0], "Could not find a supported context for: 'abcde'")

    def test_saveImage_pathList(self):
        self.makeTestDrawing()
        with self.assertRaises(TypeError) as cm:
            drawBot.saveImage(["foo.abcde"], foo=123)
        self.assertEqual(
            cm.exception.args[0],
            "Cannot apply saveImage options to multiple output formats, expected 'str' or 'os.PathLike', got 'list'",
        )

    def test_saveImage_png_multipage(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".png", multipage=False)
        self.assertEqual(output.lines(), [])

    def test_saveImage_png_ffmpegCodec(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".png", ffmpegCodec="mpeg4")
        self.assertEqual(
            output.lines(),
            ["*** DrawBot warning: Unrecognized saveImage() option found for PNGContext: ffmpegCodec ***"],
        )

    def test_saveImage_mp4_ffmpegCodec(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", ffmpegCodec="mpeg4")
        self.assertEqual(output.lines(), [])

    def test_saveImage_mp4_imageResolution(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", imageResolution=36)
        self.assertEqual(output.lines(), [])

    def test_saveImage_mp4_imagePNGGamma(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", imagePNGGamma=0.5)
        self.assertEqual(output.lines(), [])

    def test_saveImage_mp4_imageJPEGCompressionFactor(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", imageJPEGCompressionFactor=0.5)
        self.assertEqual(
            output.lines(),
            [
                "*** DrawBot warning: Unrecognized saveImage() option found for MP4Context: imageJPEGCompressionFactor ***"
            ],
        )

    def test_saveImage_mp4_multipage(self):
        self.makeTestDrawing()
        with StdOutCollector(captureStdErr=True) as output:
            self._saveImageAndReturnSize(".mp4", multipage=True)
        self.assertEqual(
            output.lines(), ["*** DrawBot warning: Unrecognized saveImage() option found for MP4Context: multipage ***"]
        )

    def test_saveImage_multipage_positionalArgument(self):
        self.makeTestDrawing()
        with TempFile(suffix=".png") as tmp:
            with StdOutCollector(captureStdErr=True) as output:
                drawBot.saveImage(tmp.path, False)
        self.assertEqual(
            output.lines(),
            [
                "*** DrawBot warning: 'multipage' should be a keyword argument: use 'saveImage(path, multipage=True)' ***"
            ],
        )

    def test_saveImage_multiplePositionalArguments(self):
        self.makeTestDrawing()
        with self.assertRaises(TypeError):
            drawBot.saveImage("*", False, "foo")

    def test_saveImage_multipage_keywordArgument(self):
        self.makeTestDrawing()
        with TempFile(suffix=".png") as tmp:
            with StdOutCollector(captureStdErr=True) as output:
                drawBot.saveImage(tmp.path, multipage=False)
        self.assertEqual(output.lines(), [])

    def test_saveImage_PIL(self):
        self.makeTestDrawing()
        image = drawBot.saveImage("PIL")
        self.assertIsInstance(image, PIL.Image.Image)

        images = drawBot.saveImage("PIL", multipage=True)
        for image in images:
            self.assertIsInstance(image, PIL.Image.Image)

    def test_saveImage_NSImage(self):
        self.makeTestDrawing()
        image = drawBot.saveImage("NSImage")
        self.assertIsInstance(image, AppKit.NSImage)

        images = drawBot.saveImage("NSImage", multipage=True)
        for image in images:
            self.assertIsInstance(image, AppKit.NSImage)

    def test_saveImage_returnValue(self):
        self.makeTestDrawing()
        for ext in (".png", ".pdf", ".gif"):
            with TempFile(suffix=ext) as tmp:
                result = drawBot.saveImage(tmp.path)
                self.assertIsNone(result)
        for ext in ("PIL", "NSImage"):
            result = drawBot.saveImage(ext)
            self.assertIsNotNone(result)

    def test_oddPageHeight_mp4(self):
        # https://github.com/typemytype/drawbot/issues/250
        self.makeTestAnimation(1, pageWidth=200, pageHeight=201)
        with TempFile(suffix=".mp4") as tmp:
            with self.assertRaises(DrawBotError) as cm:
                drawBot.saveImage(tmp.path)
        self.assertEqual(
            cm.exception.args[0], "Exporting to mp4 doesn't support odd pixel dimensions for width and height."
        )

    def test_oddPageWidth_mp4(self):
        # https://github.com/typemytype/drawbot/issues/250
        self.makeTestAnimation(1, pageWidth=201, pageHeight=200)
        with TempFile(suffix=".mp4") as tmp:
            with self.assertRaises(DrawBotError) as cm:
                drawBot.saveImage(tmp.path)
        self.assertEqual(
            cm.exception.args[0], "Exporting to mp4 doesn't support odd pixel dimensions for width and height."
        )

    def makeTestICNSDrawing(self, formats):
        drawBot.newDrawing()
        for i, size in enumerate(formats):
            drawBot.newPage(size, size)
            f = i / (len(formats) + 1)
            drawBot.fill(f, f, 1 - f)
            drawBot.rect(0, 0, size, size)

    def test_export_icns(self):
        self.makeTestICNSDrawing([16, 32, 128, 256, 512, 1024])
        self._saveImageAndReturnSize(".icns")

    def test_export_icons_invalidPageSize(self):
        self.makeTestICNSDrawing([15])
        with self.assertRaises(DrawBotError) as cm:
            self._saveImageAndReturnSize(".icns")
        self.assertEqual(
            cm.exception.args[0],
            "The .icns can not be build with the size '15x15'. Must be either: 16x16, 32x32, 128x128, 256x256, 512x512, 1024x1024",
        )

    def test_export_svg_fallbackFont(self):
        expectedPath = os.path.join(testDataDir, "expected_svgSaveFallback.svg")
        drawBot.newDrawing()
        drawBot.newPage(100, 100)
        drawBot.fallbackFont("Courier")
        drawBot.font("Times")
        drawBot.text("a", (10, 10))

        path = os.path.join(tempTestDataDir, "svgSaveFallback.svg")
        drawBot.saveImage(path)
        self.assertEqual(
            readData(path), readData(expectedPath), "Files %r and %s are not the same" % (path, expectedPath)
        )

    def test_linkURL_svg(self):
        expectedPath = os.path.join(testDataDir, "expected_svgLinkURL.svg")
        drawBot.newDrawing()
        drawBot.newPage(200, 200)
        drawBot.rect(10, 10, 20, 20)
        drawBot.linkURL("http://drawbot.com", (10, 10, 20, 20))

        path = os.path.join(tempTestDataDir, "svgLinkURL.svg")
        drawBot.saveImage(path)
        self.assertEqual(
            readData(path), readData(expectedPath), "Files %r and %s are not the same" % (path, expectedPath)
        )

    def test_formattedStringURL_svg(self):
        expectedPath = os.path.join(testDataDir, "expected_formattedStringURL.svg")
        drawBot.newDrawing()
        drawBot.newPage(200, 200)
        drawBot.underline("single")
        drawBot.url("http://drawbot.com")
        drawBot.text("foo", (10, 10))

        path = os.path.join(tempTestDataDir, "formattedStringURL.svg")
        drawBot.saveImage(path)
        self.assertEqual(
            readData(path), readData(expectedPath), "Files %r and %s are not the same" % (path, expectedPath)
        )

    def test_export_color_space_cmyk(self):
        drawBot.newDrawing()
        drawBot.size(1000, 1000)
        drawBot.cmykFill(1, 0, 0, 0)
        drawBot.rect(0, 0, 250, 1000)
        drawBot.cmykFill(0, 1, 0, 0)
        drawBot.rect(250, 0, 250, 1000)
        drawBot.cmykFill(0, 0, 1, 0)
        drawBot.rect(500, 0, 250, 1000)
        drawBot.cmykFill(0, 0, 0, 1)
        drawBot.rect(750, 0, 250, 1000)

        rgba_path = os.path.join(tempTestDataDir, "cmyk_export_default.tiff")
        cmyk_path = os.path.join(tempTestDataDir, "cmyk_export_with_color_space.tiff")
        cmyk_with_profile_path = os.path.join(tempTestDataDir, "cmyk_export_with_color_space_and_profile.tiff")

        drawBot.saveImage(rgba_path)
        drawBot.saveImage(cmyk_path, colorSpace="CMYK")

        icc_data = AppKit.NSData.dataWithContentsOfFile_("/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc")
        drawBot.saveImage(cmyk_with_profile_path, colorSpace="CMYK", imageColorSyncProfileData=icc_data)

        drawBot.endDrawing()

        rgba_image = PIL.Image.open(rgba_path)
        self.assertEqual(rgba_image.mode, "RGBA")

        rgba_image_profile = ImageCms.ImageCmsProfile(
            io.BytesIO(rgba_image.info.get("icc_profile"))
        )
        self.assertEqual(
            rgba_image_profile.profile.profile_description,
            "Generic RGB Profile"
        )

        cmyk_image = PIL.Image.open(cmyk_path)
        self.assertEqual(cmyk_image.mode, "CMYK")
        self.assertIsNone(cmyk_image.info.get("icc_profile"))

        cmyk_with_profile_image = PIL.Image.open(cmyk_with_profile_path)
        self.assertEqual(cmyk_with_profile_image.mode, "CMYK")
        cmyk_with_profile_image_profile = ImageCms.ImageCmsProfile(
            io.BytesIO(cmyk_with_profile_image.info.get("icc_profile"))
        )
        self.assertEqual(
            cmyk_with_profile_image_profile.profile.profile_description,
            "Generic CMYK Profile"
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    sys.exit(unittest.main())
