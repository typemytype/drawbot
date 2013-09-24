# create a new empty path
newPath()
# set the first oncurve point
moveTo((100, 100))
# line to from the previous point to a new point
lineTo((100, 200))
lineTo((200, 200))

# curve to a point with two given handles
curveTo((200, 100), (150, 100), (100, 100))

# close the path
closePath()
# draw the path
drawPath()
