from __future__ import division, absolute_import, print_function

import os

from drawBot.misc import executeExternalProcess, getExternalToolPath


ffmpegPath = getExternalToolPath(os.path.dirname(__file__), "ffmpeg")


def generateMP4(imageTemplate, mp4path, frameRate):
    assert ffmpegPath is not None
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
    executeExternalProcess(cmds)
