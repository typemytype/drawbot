# set no fill
fill(None)
# set the stroke color to black
stroke(0)
# set a stroke width
strokeWidth(10)
# set a miter limit
miterLimit(30)

# create a bezier path
path = BezierPath()
# move to a point
path.moveTo((100, 100))
# line to a point
path.lineTo((100, 200))
path.lineTo((110, 100))

# set a line join style
lineJoin("miter")
# draw the path
drawPath(path)
# translate the canvas
translate(100, 0)

# set a line join style
lineJoin("round")
# draw the path
drawPath(path)
# translate the canvas
translate(100, 0)

# set a line join style
lineJoin("bevel")
# draw the path
drawPath(path)
# translate the canvas
translate(100, 0)