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

    def test_ffmpegCodec(self):
        self.makeTestAnimation()
        fd, mp4_tmp = tempfile.mkstemp(suffix=".mp4")

        try:
            drawBot.saveImage(mp4_tmp)
            s = os.stat(mp4_tmp)
            size_h264 = s.st_size
        finally:
            os.remove(mp4_tmp)

        try:
            drawBot.saveImage(mp4_tmp, ffmpegCodec="mpeg4")
            s = os.stat(mp4_tmp)
            size_mpeg4 = s.st_size
        finally:
            os.remove(mp4_tmp)

        self.assertLess(size_h264, size_mpeg4)

    def test_export_mov(self):
        self.makeTestAnimation(5)
        fd, mov_tmp = tempfile.mkstemp(suffix=".mov")
        try:
            drawBot.saveImage(mov_tmp)
        finally:
            os.remove(mov_tmp)

    def test_export_gif(self):
        self.makeTestAnimation(5)
        fd, gif_tmp = tempfile.mkstemp(suffix=".gif")
        try:
            drawBot.saveImage(gif_tmp)
        finally:
            os.remove(gif_tmp)


if __name__ == '__main__':
    sys.exit(unittest.main())
