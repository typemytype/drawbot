# create a path
path = BezierPath()

# move to a point
path.moveTo((100, 100))
# line to a point
path.lineTo((100, 200))

# set stroke color to black
stroke(0)
# set no fill
fill(None)
# set the width of the stroke
strokeWidth(10)

# set a line dash
lineDash(5, 2)

# draw the path
drawPath(path)

# move the canvas
translate(100, 0)

# set a different line dash
lineDash(5, 2, 3, 10, 1)

# draw the same path again
drawPath(path)