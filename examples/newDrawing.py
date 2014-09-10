# draw a rectangle
rect(10, 10, width()-20, height()-20)
# save it as a pdf
saveImage("~/Deskopt/aRect.pdf")

# reset the drawing stack to a clear and empty stack
newDrawing()

# draw an oval
oval(10, 10, width()-20, height()-20)
# save it as a pdf
saveImage("~/Deskopt/anOval.pdf")