# set a blend mode
blendMode("multiply")

# set a color
cmykFill(1, 0, 0, 0)
# draw a rectangle
rect(10, 10, 100, 100)
# set an other color
cmykFill(0, 1, 0, 0)
# overlap a second rectangle
rect(60, 60, 100, 100)