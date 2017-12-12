from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
import sys
import os
import unittest
import tempfile
import drawBot
import random


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
        self._saveImageAndReturnSize(".png", someArbitraryOption="foo")

    def test_export_mov(self):
        self.makeTestAnimation(5)
        self._saveImageAndReturnSize(".mov")

    def test_export_gif(self):
        self.makeTestAnimation(5)
        self._saveImageAndReturnSize(".gif")


if __name__ == '__main__':
    sys.exit(unittest.main())
