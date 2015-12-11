import AppKit
import Quartz

import sys
import os
import tempfile
import subprocess

from imageContext import ImageContext

gifsiclePath = os.path.join(os.path.dirname(__file__), "tools", "gifsicle")
if not os.path.exists(gifsiclePath):
    gifsiclePath = os.path.join(os.getcwd(), "tools", "gifsicle")


class GifContext(ImageContext):

    _saveImageFileTypes = {
        "gif": AppKit.NSGIFFileType,
        }

    fileExtensions = _saveImageFileTypes.keys()

    _delay = 10

    def __init__(self):
        super(GifContext, self).__init__()
        self._delayData = []

    def _frameDuration(self, seconds):
        # gifsicle -h: Set frame delay to TIME (in 1/100sec).
        self._delayData[-1] = int(seconds * 100)

    def _newPage(self, width, height):
        super(GifContext, self)._newPage(width, height)
        self._delayData.append(self._delay)

    def _writeDataToFile(self, data, path, multipage):
        pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
        pageCount = pdfDocument.pageCount()
        shouldBeAnimated = pageCount > 1

        tempPath = path
        if shouldBeAnimated:
            tempPath = tempfile.mkstemp(suffix=".gif")[1]

        inputPaths = super(GifContext, self)._writeDataToFile(data, tempPath, shouldBeAnimated)

        if shouldBeAnimated:
            cmds = [
                # gifsicle path
                gifsiclePath,
                # optimize level
                # "-O3",
                # ignore warnings
                "-w",
                # force to 256 colors
                "--colors", "256",
                # make it loop
                "--loop",
            ]
            # add source paths with delay for each frame
            for i, inputPath in enumerate(inputPaths):
                cmds += [
                        # add the frame duration
                        "--delay", "%i" % self._delayData[i],
                        # add the input gif for each frame
                        inputPath
                    ]

            cmds += [
                # output path
                "--output",
                path
            ]

            # make a string of escaped commands
            cmds = subprocess.list2cmdline(cmds)

            gifsicleStdOut = tempfile.TemporaryFile()
            gifsicleStdErr = tempfile.TemporaryFile()
            try:
                # go
                result = subprocess.Popen(cmds, stdout=gifsicleStdOut, stderr=gifsicleStdErr, shell=True)
                resultCode = result.wait()
                if resultCode != 0:
                    gifsicleStdOut.seek(0)
                    gifsicleStdErr.seek(0)
                    sys.stdout.write(gifsicleStdOut.read())
                    sys.stderr.write(gifsicleStdErr.read())
                    raise RuntimeError("gifsicle failed with error code %s" % resultCode)
            finally:
                gifsicleStdOut.close()
                gifsicleStdErr.close()
                # remove the temp input gifs
                for inputPath in inputPaths:
                    os.remove(inputPath)
