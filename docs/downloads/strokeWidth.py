# set no fill
fill(None)
# set black as the stroke color
stroke(0)
# loop over a range of 10
for i in range(10):
    # in each loop set the stroke width
    strokeWidth(i)
    # draw a line
    line((100, 100), (200, 200))
    # and translate the canvas
    translate(15, 0)