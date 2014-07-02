# path to the image
path = u"http://f.cl.ly/items/1T3x1y372J371p0v1F2Z/drawBot.jpg"

# get the size of the image
w, h = imageSize(path)

# setup a variable for the font size as for the steps
s = 15

# shift it up a bit
translate(100, 100)

# set a font with a size
font("Helvetica-Bold")
fontSize(s)

# loop over the width of the image
for x in range(0, w, s):
    # loop of the height of the image
    for y in range(0, h, s):
        # get the color
        color = imagePixelColor(path, (x, y))
        if color:
            r, g, b, a = color
            # set the color
            fill(r, g, b, a)
            # draw some text
            text("W", (x, y))
