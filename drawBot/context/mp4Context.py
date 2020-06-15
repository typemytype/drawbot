import os
import tempfile
import shutil

from drawBot.misc import warnings

from .imageContext import PNGContext

from .tools.mp4Tools import generateMP4


class MP4Context(PNGContext):

    fileExtensions = ["mp4"]

    saveImageOptions = [
        ("ffmpegCodec", "The codec to be used by ffmpeg. By default it is 'libx264' (for H.264). The 'mpeg4' codec gives better results when importing the movie into After Effects, at the expense of a larger file size."),
    ] + [(key, doc) for key, doc in PNGContext.saveImageOptions if key != "multipage"]

    _defaultFrameDuration = 1 / 10

    ensureEvenPixelDimensions = True

    def __init__(self):
        super(MP4Context, self).__init__()
        self._frameDurations = []

    def _frameDuration(self, frameDuration):
        self._frameDurations[-1] = frameDuration

    def _newPage(self, width, height):
        super(MP4Context, self)._newPage(width, height)
        self._frameDurations.append(self._defaultFrameDuration)
        # https://github.com/typemytype/drawbot/issues/391
        # draw a solid white background by default
        # ffmpeg converts transparency to a black background color
        self.save()
        self.fill(1)
        self.rect(0, 0, width, height)
        self.restore()

    def _writeDataToFile(self, data, path, options):
        frameRate = round(1.0 / self._frameDurations[0], 3)
        frameDurations = set(self._frameDurations)
        if len(frameDurations) > 1:
            warnings.warn("Exporting to mp4 doesn't support varying frame durations, only the first value was used.")
        options["multipage"] = True
        codec = options.get("ffmpegCodec", "libx264")
        tempDir = tempfile.mkdtemp(suffix=".mp4tmp")
        try:
            super(MP4Context, self)._writeDataToFile(data, os.path.join(tempDir, "frame.png"), options)
            generateMP4(os.path.join(tempDir, "frame_%d.png"), path, frameRate, codec)
        finally:
            shutil.rmtree(tempDir)
