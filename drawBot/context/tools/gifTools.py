import AppKit
import shutil
import os
import tempfile

from drawBot.misc import executeExternalProcess, getExternalToolPath


def generateGif(sourcePaths, destPath, delays, loop=True):
    gifsiclePath = getExternalToolPath(os.path.dirname(__file__), "gifsicle")
    assert gifsiclePath is not None
    cmds = [
        # gifsicle path
        gifsiclePath,
        # optimize level
        # "-O3",
        # ignore warnings
        "-w",
        # force to 256 colors
        "--colors", "256",
    ]
    if loop:
        # make it loop
        cmds.append("--loop")
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
    executeExternalProcess(cmds)
    # remove the temp input gifs
    for inputPath in sourcePaths:
        os.remove(inputPath)


_explodedGifCache = {}


def _explodeGif(path):
    gifsiclePath = getExternalToolPath(os.path.dirname(__file__), "gifsicle")
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
    executeExternalProcess(cmds, cwd=destRoot)
    files = os.listdir(destRoot)
    _explodedGifCache[path] = dict(
        source=destRoot,
        fileNames=sorted(files),
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
