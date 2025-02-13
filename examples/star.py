from math import cos, pi, sin

import drawBot as db


def star(center, points, inner, outer):
    # create a new path
    db.newPath()
    # move the pen to the initial position
    X, Y = center
    db.moveTo((X, Y + outer))
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
        db.lineTo((x, y))
    db.closePath()
    db.drawPath()


if __name__ == "__main__":
    star((312, 344), 5, 60, 110)
