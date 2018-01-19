def star(center, points, inner, outer):
    # create a new path
    newPath()
    # move the pen to the initial position
    X, Y = center
    moveTo((X, Y + outer))
    for i in range(1, int(2 * points)):
        angle = i * pi / points
        x = sin(angle)
        y = cos(angle)
        if i % 2:
            radius = inner
        else:
            radius = outer
        x = X + radius * x
        y = Y + radius * y
        lineTo((x, y))
    closePath()
    drawPath()

star((312, 344), 5, 60, 110)
