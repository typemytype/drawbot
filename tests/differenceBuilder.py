import os
from PIL import Image, ImageChops
import tempfile

from testSupport import compareImages, testDataDir

import drawBot
import sys

if len(sys.argv) == 3:
    root = sys.argv[1]
    dest = sys.argv[2]
else:
    from vanilla import dialogs
    root = dialogs.getFolder()[0]
    dest = dialogs.putFile(["pdf"])

tests = [os.path.join(root, filename) for filename in os.listdir(root) if os.path.splitext(filename)[-1].lower() == ".png"]

drawBot.newDrawing()
for path in tests:
    fileName = os.path.basename(path)
    if not fileName.startswith("example_"):
        fileName = "expected_" + fileName

    localPath = os.path.join(testDataDir, fileName)
    if not os.path.exists(localPath):
        continue
    w, h = drawBot.imageSize(path)
    a = compareImages(localPath, path)
    padding = 0
    if a > 0.0012:
        padding = 50
    pathPadding = 30
    drawBot.newPage(w * 4 + padding * 2, h + padding * 2 + pathPadding)
    drawBot.translate(0, pathPadding)
    if padding:
        with drawBot.savedState():
            drawBot.fill(None)
            drawBot.stroke(1, 0, 0)
            drawBot.strokeWidth(padding * 2)
            drawBot.rect(0, 0, drawBot.width(), drawBot.height())
        drawBot.translate(padding, padding)

    drawBot.text(f"{os.path.basename(path)} - {os.path.basename(localPath)}", (10, 10 - padding - pathPadding))

    drawBot.image(path, (0, 0))
    drawBot.image(localPath, (w, 0))

    im1 = Image.open(path)
    im2 = Image.open(localPath)
    diff = ImageChops.difference(im1, im2)
    with tempfile.NamedTemporaryFile("wb", suffix=".png") as f:
        diff.save(f, "png")
        imDiff = drawBot.ImageObject(f.name)
        drawBot.image(imDiff, (w*2, 0))

    hist = diff.histogram()

    redPath = drawBot.BezierPath()
    greenPath = drawBot.BezierPath()
    bluePath = drawBot.BezierPath()
    alphaPath = drawBot.BezierPath()
    reds = hist[0:256]
    greens = hist[256:512]
    blues = hist[512:768]
    alphas = hist[768:1024]

    redPath.moveTo((0, 0))
    greenPath.moveTo((0, 0))
    bluePath.moveTo((0, 0))
    alphaPath.moveTo((0, 0))
    for i in range(256):
        x = w * (i / 255)
        redPath.lineTo((x, h * (reds[i]/255)))
        greenPath.lineTo((x, h * (greens[i]/255)))
        bluePath.lineTo((x, h * (blues[i]/255)))
        alphaPath.lineTo((x, h * (alphas[i]/255)))

    redPath.lineTo((w, 0))
    greenPath.lineTo((w, 0))
    bluePath.lineTo((w, 0))
    alphaPath.lineTo((w, 0))

    redPath.closePath()
    greenPath.closePath()
    bluePath.closePath()
    alphaPath.closePath()

    drawBot.translate(w*3, 0)
    drawBot.scale(.25, 1)
    drawBot.fill(1, 0, 0)
    drawBot.drawPath(redPath)

    drawBot.translate(w, 0)
    drawBot.fill(0, 1, 0)
    drawBot.drawPath(greenPath)

    drawBot.translate(w, 0)
    drawBot.fill(0, 0, 1)
    drawBot.drawPath(bluePath)

    drawBot.translate(w, 0)
    drawBot.fill(0, 0, 0)
    drawBot.drawPath(alphaPath)


drawBot.saveImage(dest)
