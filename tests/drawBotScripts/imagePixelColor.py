# This is a test case derived from https://github.com/typemytype/drawbot/issues/171
# It ensures that rgb values specified in fill() end up in image output without
# being mangled by a color space (within 8-bit resulution).

from drawBot import *
from PIL import Image

canvasSize = 400
size(canvasSize, canvasSize)

# colorSpace("sRGB")
# colorSpace("genericRGB")
# colorSpace("adobeRGB1998")

bands = 4
bandWidth = canvasSize / bands

fontSize(10)

for i in range(bands):
    x = i * bandWidth
    for j in range(bands):
        y = j * bandWidth
        r = i / bands
        g = j / bands
        b = 0.5
        fill(r, g, b)
        rect(x, y, bandWidth, bandWidth)
        fill(0)
        text("%s,%s,%s" % (r, g, b), (x + 3, y + 5))

fn = "../tempTestData/tmp_imagePixelColor.png"
saveImage(fn)

im = Image.open(fn)

for i in range(bands):
    x = (i + 0.5) * bandWidth
    for j in range(bands):
        y = (j + 0.5) * bandWidth
        r, g, b, a = imagePixelColor(fn, (x, y))
        print(" CG:", round(r, 4), round(g, 4), round(b, 4))
        r, g, b, a = im.getpixel((x, canvasSize - y))
        print("PIL:", round(r/255, 4), round(g/255, 4), round(b/255, 4))
        print()
