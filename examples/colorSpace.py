# set a color 
r, g, b, a = 0.74, 0.51, 1.04, 1

# get all available color spaces
colorSpaces = listColorSpaces()

x = 0
w = width() / len(colorSpaces)

# start loop
for space in colorSpaces:

    # set a color space
    colorSpace(space)
    # set the color
    fill(r, g, b)
    # draw a rect
    rect(x, 0, w, height())
    x += w