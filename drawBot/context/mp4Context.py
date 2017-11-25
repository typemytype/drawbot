from __future__ import division, absolute_import, print_function

import sys
import os
import tempfile
import shutil
import subprocess
from drawBot.misc import warnings

import AppKit

from .imageContext import ImageContext


ffmpegPath = os.path.join(os.path.dirname(__file__), "tools", "ffmpeg")
if not os.path.exists(ffmpegPath):
    ffmpegPath = AppKit.NSBundle.mainBundle().pathForResource_ofType_("ffmpeg", None)


def _executeCommand(cmds, cwd=None):
    stdout = tempfile.TemporaryFile(mode="w+")
    stderr = tempfile.TemporaryFile(mode="w+")
    try:
        # go
        resultCode = subprocess.call(cmds, stdout=stdout, stderr=stderr, cwd=cwd)
        if resultCode != 0:
            stdout.seek(0)
            stderr.seek(0)
            sys.stdout.write(stdout.read())
            sys.stderr.write(stderr.read())
            raise RuntimeError("ffmpeg failed with error code %s" % resultCode)
    finally:
        stdout.close()
        stderr.close()


def generateMP4(imageTemplate, mp4path, frameRate):
    cmds = [
        # ffmpeg path
        ffmpegPath,
        "-y",                   # overwrite existing files
        "-loglevel", "0",       # quiet
        "-r", str(frameRate),   # frame rate
        "-i", imageTemplate,    # input sequence
        "-c:v", "libx264",      # codec
        "-crf", "20", "-pix_fmt", "yuv420p",  # dunno
        mp4path,                # output path
    ]
    _executeCommand(cmds)


class MP4Context(ImageContext):

    _saveImageFileTypes = {
        "png": AppKit.NSPNGFileType,
    }

    fileExtensions = ["mp4"]

    _defaultFrameDuration = 1/10

    def __init__(self):
        super(MP4Context, self).__init__()
        self._frameDurations = []

    def _frameDuration(self, frameDuration):
        self._frameDurations[-1] = frameDuration

    def _newPage(self, width, height):
        super(MP4Context, self)._newPage(width, height)
        self._frameDurations.append(self._defaultFrameDuration)

    def _writeDataToFile(self, data, path, multipage):
        frameRate = round(1.0 / self._frameDurations[0], 3)
        frameDurations = set(self._frameDurations)
        if len(frameDurations) > 1:
            warnings.warn("Exporting to mp4 doesn't support varying frame durations, only the first value was used.")

        tempDir = tempfile.mkdtemp(suffix=".mp4tmp")
        try:
            super(MP4Context, self)._writeDataToFile(data, os.path.join(tempDir, "frame.png"), True)
            generateMP4(os.path.join(tempDir, "frame_%d.png"), path, frameRate)
        finally:
            shutil.rmtree(tempDir)
