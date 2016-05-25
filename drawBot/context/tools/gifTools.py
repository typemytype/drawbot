import AppKit

import shutil
import os
import tempfile
import subprocess
import sys


gifsiclePath = os.path.join(os.path.dirname(__file__), "gifsicle")
if not os.path.exists(gifsiclePath):
    gifsiclePath = os.path.join(os.getcwd(), "gifsicle")


def _executeCommand(cmds, cwd=None):
    gifsicleStdOut = tempfile.TemporaryFile()
    gifsicleStdErr = tempfile.TemporaryFile()
    try:
        # go
        resultCode = subprocess.call(cmds, stdout=gifsicleStdOut, stderr=gifsicleStdErr, cwd=cwd)
        if resultCode != 0:
            gifsicleStdOut.seek(0)
            gifsicleStdErr.seek(0)
            sys.stdout.write(gifsicleStdOut.read())
            sys.stderr.write(gifsicleStdErr.read())
            raise RuntimeError("gifsicle failed with error code %s" % resultCode)
    finally:
        gifsicleStdOut.close()
        gifsicleStdErr.close()


def generateGif(sourcePaths, destPath, delays):
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
    for i, inputPath in enumerate(sourcePaths):
        cmds += [
                # add the frame duration
                "--delay", "%i" % delays[i],
                # add the input gif for each frame
                inputPath
            ]

    cmds += [
        # output path
        "--output",
        destPath
    ]
    _executeCommand(cmds)
    # remove the temp input gifs
    for inputPath in sourcePaths:
        os.remove(inputPath)


_explodedGifCache = {}


def _explodeGif(path):
    if isinstance(path, AppKit.NSURL):
        path = path.path()
    destRoot = tempfile.mkdtemp()
    cmds = [
        gifsiclePath,
        # explode
        "--explode",
        # source path
        path
        ]
    _executeCommand(cmds, cwd=destRoot)
    files = os.listdir(destRoot)
    _explodedGifCache[path] = dict(
            source=destRoot,
            fileNames=files,
        )


def clearExplodedGifCache():
    for path, info in _explodedGifCache.items():
        shutil.rmtree(info["source"])
    _explodedGifCache.clear()


def gifFrameCount(path):
    if isinstance(path, AppKit.NSURL):
        path = path.path()
    if path not in _explodedGifCache:
        _explodeGif(path)
    frameCount = len(_explodedGifCache[path]["fileNames"])
    if frameCount == 0:
        return None
    return frameCount


def gifFrameAtIndex(path, index):
    if isinstance(path, AppKit.NSURL):
        path = path.path()
    if path not in _explodedGifCache:
        _explodeGif(path)
    source = _explodedGifCache[path]["source"]
    fileNames = _explodedGifCache[path]["fileNames"]
    fileName = os.path.join(source, fileNames[index])
    url = AppKit.NSURL.fileURLWithPath_(fileName)
    return AppKit.NSImage.alloc().initByReferencingURL_(url)
