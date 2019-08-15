import os

from drawBot.misc import executeExternalProcess, getExternalToolPath


def generateMP4(imageTemplate, mp4path, frameRate, codec="libx264"):
    ffmpegPath = getExternalToolPath(os.path.dirname(__file__), "ffmpeg")
    assert ffmpegPath is not None
    cmds = [
        # ffmpeg path
        ffmpegPath,
        "-y",                   # overwrite existing files
        "-loglevel", "16",      # 'error, 16' Show all errors, including ones which can be recovered from.
        "-r", str(frameRate),   # frame rate
        "-i", imageTemplate,    # input sequence
        "-c:v", codec,          # codec
        "-crf", "20",           # Constant Rate Factor
        "-pix_fmt", "yuv420p",  # pixel format
        mp4path,                # output path
    ]
    executeExternalProcess(cmds)
