# initiate a new image object
im = ImageObject()

# draw in the image
# the 'with' statement will create a custom context
# only drawing in the image object
with im:
    # set a size for the image
    size(200, 200)
    # draw something
    fill(1, 0, 0)
    rect(0, 0, width(), height())
    fill(1)
    fontSize(30)
    text("Hello World", (10, 10))

# draw in the image in the main context
image(im, (10, 50))
# apply some filters
im.gaussianBlur()

# get the offset (with a blur this will be negative)
x, y = im.offset()
# draw in the image in the main context
image(im, (300+x, 50+y))