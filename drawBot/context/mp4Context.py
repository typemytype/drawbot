from __future__ import division, absolute_import, print_function

import os
import tempfile
import shutil
from drawBot.misc import warnings

import AppKit

from .imageContext import ImageContext

from .tools.mp4Tools import generateMP4


class MP4Context(ImageContext):

    _saveImageFileTypes = {
        "png": AppKit.NSPNGFileType,
    }

    fileExtensions = ["mp4"]

    _defaultFrameDuration = 1 / 10

    def __init__(self):
        super(MP4Context, self).__init__()
        self._frameDurations = []

    def _frameDuration(self, frameDuration):
        self._frameDurations[-1] = frameDuration

    def _newPage(self, width, height):
        super(MP4Context, self)._newPage(width, height)
        self._frameDurations.append(self._defaultFrameDuration)

    def _writeDataToFile(self, data, path, multipage, options):
        frameRate = round(1.0 / self._frameDurations[0], 3)
        frameDurations = set(self._frameDurations)
        if len(frameDurations) > 1:
            warnings.warn("Exporting to mp4 doesn't support varying frame durations, only the first value was used.")

        tempDir = tempfile.mkdtemp(suffix=".mp4tmp")
        try:
            super(MP4Context, self)._writeDataToFile(data, os.path.join(tempDir, "frame.png"), True, options)
            generateMP4(os.path.join(tempDir, "frame_%d.png"), path, frameRate)
        finally:
            shutil.rmtree(tempDir)
