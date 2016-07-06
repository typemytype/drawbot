# create a bezier path
path = BezierPath()

# move to a point
path.moveTo((100, 100))
# line to a point
path.lineTo((100, 200))
path.lineTo((200, 200))
# close the path
path.closePath()

# loop over a range of 10
for i in range(10):
    # set a random color with alpha value of .3
    fill(random(), random(), random(), .3)
    # in each loop draw the path
    drawPath(path)
    # translate the canvas
    translate(5, 5)

path.text("Hello world", font="Helvetica", fontSize=30, offset=(210, 210))

print "All Points:"
print path.points

print "On Curve Points:"
print path.onCurvePoints

print "Off Curve Points:"
print path.offCurvePoints

# print out all points from all segments in all contours
for contour in path.contours:
    for segment in contour:
        for x, y in segment:
            print x, y
    print "is open:", contour.open

# translate the path
path.translate(0, 300)
# draw the path again
drawPath(path)
