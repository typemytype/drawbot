# create a bezier path
path = BezierPath()

# move to a point
path.moveTo((100, 100))
# line to a point
path.lineTo((100, 200))
path.lineTo((200, 200))
# close the path
path.closePath()
# set the path as a clipping path
clipPath(path)
# the oval will be clipped inside the path
oval(100, 100, 100, 100)


