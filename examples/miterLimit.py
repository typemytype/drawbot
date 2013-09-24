# create a path
path = BezierPath()

# move to a point
path.moveTo((100, 100))
# line to a point
path.lineTo((100, 200))
path.lineTo((120, 100))

# set stroke color to black
stroke(0)
# set no fill
fill(None)
# set the width of the stroke
strokeWidth(10)

# draw the path
drawPath(path)

# move the canvas
translate(100, 0)

# set a miter limit
miterLimit(50)

# draw the same path again
drawPath(path)