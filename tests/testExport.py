from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import sys
import os
import unittest
import tempfile
import glob
import drawBot
import random
import AppKit
from drawBot.context.tools.gifTools import gifFrameCount


class ExportTest(unittest.TestCase):

    def makeTestAnimation(self, numFrames=25):
        random.seed(0)
        drawBot.newDrawing()
        for i in range(numFrames):
            drawBot.newPage(500, 500)
            drawBot.frameDuration(1/25)
            drawBot.fill(1)
            drawBot.rect(0, 0, 500, 500)
            drawBot.fill(0)
            drawBot.rect(random.randint(0, 100), random.randint(0, 100), 400, 400)

    def makeTestDrawing(self):
        drawBot.newDrawing()
        drawBot.newPage(500, 500)
        drawBot.oval(100, 100, 300, 300)

    def _saveImageAndReturnSize(self, extension, **options):
        fd, tmp = tempfile.mkstemp(suffix=extension)
        try:
            drawBot.saveImage(tmp, **options)
            fileSize = os.stat(tmp).st_size
        finally:
            os.remove(tmp)
        return fileSize

    def test_ffmpegCodec(self):
        self.makeTestAnimation()
        size_h264 = self._saveImageAndReturnSize(".mp4")
        size_mpeg4 = self._saveImageAndReturnSize(".mp4", ffmpegCodec="mpeg4")
        self.assertLess(size_h264, size_mpeg4, "encoded with h264 is expected to be smaller than with mpeg4")

    def test_arbitraryOption(self):
        self.makeTestAnimation(1)
        # This issues a warning (as it should), but unittest is either suppressing that or fine with it.
        self._saveImageAndReturnSize(".png", someArbitraryOption="foo")

    def test_export_mov(self):
        self.makeTestAnimation(5)
        self._saveImageAndReturnSize(".mov")

    def test_export_gif(self):
        self.makeTestAnimation(5)
        self._saveImageAndReturnSize(".gif")

    def test_imageResolution(self):
        self.makeTestDrawing()
        fd, tmp = tempfile.mkstemp(suffix=".png")
        try:
            drawBot.saveImage(tmp)
            self.assertEqual(drawBot.imageSize(tmp), (500, 500))
            drawBot.saveImage(tmp, imageResolution=144)
            self.assertEqual(drawBot.imageSize(tmp), (1000, 1000))
            drawBot.saveImage(tmp, imageResolution=36)
            self.assertEqual(drawBot.imageSize(tmp), (250, 250))
            drawBot.saveImage(tmp, imageResolution=18)
            self.assertEqual(drawBot.imageSize(tmp), (125, 125))
        finally:
            os.remove(tmp)

    def test_imageJPEGCompressionFactor(self):
        self.makeTestDrawing()
        lowCompressionSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=1.0)
        progressiveSize = self._saveImageAndReturnSize(".jpg", imageJPEGCompressionFactor=1.0, imageJPEGProgressive=True)
        self.assertGreater(lowCompressionSize, progressiveSize)
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
        fd, tmp1 = tempfile.mkstemp(suffix=".jpg")
        fd, tmp2 = tempfile.mkstemp(suffix=".jpg")
        fd, tmp3 = tempfile.mkstemp(suffix=".jpg")
        try:
            drawBot.saveImage(tmp1, imageJPEGCompressionFactor=1.0)
            self.assertEqual(drawBot.imagePixelColor(tmp1, (5, 5)), (1.0, 1.0, 1.0, 1.0))
            drawBot.saveImage(tmp2, imageJPEGCompressionFactor=1.0, imageFallbackBackgroundColor=(0, 1, 0))
            r, g, b, a = drawBot.imagePixelColor(tmp2, (5, 5))
            self.assertEqual((round(r, 2), round(g, 2), round(b, 2)), (0, 0.97, 0))  # XXX 0.97 vs 1.0 "calibrated" vs "device"
            drawBot.saveImage(tmp3, imageJPEGCompressionFactor=1.0, imageFallbackBackgroundColor=AppKit.NSColor.redColor())
            r, g, b, a = drawBot.imagePixelColor(tmp3, (5, 5))
            self.assertEqual((round(r, 2), round(g, 2), round(b, 2)), (1, 0.15, 0))
        finally:
            os.remove(tmp1)
            os.remove(tmp2)
            os.remove(tmp3)

    def _testMultipage(self, extension, expectedMultipageCount):
        self.makeTestAnimation(5)
        tmp = tempfile.mktemp(suffix=extension)
        base, ext = os.path.splitext(tmp)
        pattern = base + "_*" + ext
        self.assertEqual(len(glob.glob(pattern)), 0)
        try:
            drawBot.saveImage(tmp)
            self.assertEqual(len(glob.glob(pattern)), 0)
            drawBot.saveImage(tmp, multipage=False)
            self.assertEqual(len(glob.glob(pattern)), 0)
            drawBot.saveImage(tmp, multipage=True)
            self.assertEqual(len(glob.glob(pattern)), expectedMultipageCount)
        finally:
            os.remove(tmp)
            for path in glob.glob(pattern):
                os.remove(path)

    def test_multipage_jpg(self):
        self._testMultipage(".png", 5)

    def test_multipage_jpg(self):
        self._testMultipage(".jpg", 5)

    def test_multipage_svg(self):
        self._testMultipage(".svg", 5)

    def test_multipage_gif(self):
        self._testMultipage(".gif", 0)

    def test_multipage_pdf(self):
        self._testMultipage(".pdf", 0)

    def test_animatedGIF(self):
        self.makeTestAnimation(5)
        tmp = tempfile.mktemp(suffix=".gif")
        try:
            drawBot.saveImage(tmp)
            self.assertEqual(gifFrameCount(tmp), 5)
        finally:
            os.remove(tmp)


if __name__ == '__main__':
    sys.exit(unittest.main())
