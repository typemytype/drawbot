# create a fresh bezier path
path = BezierPath()
# draw some text
# the text will be converted to curves
path.text("a", font="Helvetica-Bold", fontSize=500)
# set an indent
indent = 50
# calculate the width and height of the path
minx, miny, maxx, maxy = path.bounds()
w = maxx - minx
h = maxy - miny
# calculate the box where we want to draw the path in
boxWidth = width() - indent * 2
boxHeight = height() - indent * 2
# calculate a scale based on the given path bounds and the box
s = min([boxWidth / float(w), boxHeight / float(h)])
# translate to the middle
translate(width()*.5, height()*.5)
# set the scale
scale(s)
# translate the negative offset, letter could have overshoot
translate(-minx, -miny)
# translate with half of the width and height of the path
translate(-w*.5, -h*.5)
# draw the path
drawPath(path)
# set a font
font("Helvetica-Light")
# set a font size
fontSize(5)
# set white as color
fill(1)
# draw some text in the path
textBox("abcdefghijklmnopqrstuvwxyz"*30000, path)