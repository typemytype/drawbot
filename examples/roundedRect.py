def roundedRect(x, y, w, h, radius, radiusBottomRight=None, radiusTopRight=None, radiusTopLeft=None):
    """
    Draw a rounded rect from position `x`, `y` with given width and height and given `radius`.

    A radiuses that exceeds the width or height of the rectangle will be clipped.

    Optionally a radius could be provided for each corner the following order:
    bottom left, bottom right, top right, top left

    .. downloadcode:: roundedRect.py

        # draw a rounding rect
        #           x    y    w    h    radius
        roundedRect(100, 100, 200, 200, 10)

        #           x     y   w    h    bl  br  tr  tl
        roundedRect(100, 330, 200, 200, 10, 30, 40, 50)
    """
    # do some checking on the radiuses
    radiusBottomLeft = radius
    if radiusTopLeft is None and radiusTopRight is None and radiusBottomRight is None:
        radiusTopLeft = radiusTopRight = radiusBottomRight = radius

    if radiusBottomLeft + radiusBottomRight > w:
        diff = (radiusBottomLeft + radiusBottomRight - w) * .5
        radiusBottomLeft -= diff
        radiusBottomRight -= diff
    if radiusTopLeft + radiusTopRight > w:
        diff = (radiusTopLeft + radiusTopRight - w) * .5
        radiusTopLeft -= diff
        radiusTopRight -= diff
    if radiusBottomLeft + radiusTopLeft > h:
        diff = (radiusBottomLeft + radiusTopLeft - h) * .5
        radiusBottomLeft -= diff
        radiusTopLeft -= diff
    if radiusBottomRight + radiusTopRight > h:
        diff = (radiusBottomRight + radiusTopRight - h) * .5
        radiusBottomRight -= diff
        radiusTopRight -= diff
    
    minValue = min(w, h)

    if radiusBottomRight < 0:
        radiusBottomRight = 0
    if radiusTopRight < 0:
        radiusTopRight = 0
    if radiusBottomLeft < 0:
        radiusBottomLeft = 0
    if radiusTopLeft < 0:
        radiusTopLeft = 0

    if radiusBottomRight > minValue:
        radiusBottomRight = minValue
    if radiusTopRight > minValue:
        radiusTopRight = minValue
    if radiusBottomLeft > minValue:
        radiusBottomLeft = minValue
    if radiusTopLeft > minValue:
        radiusTopLeft = minValue

    # start drawing
    path = BezierPath()
    path.moveTo((x + radiusBottomLeft, y))
    path.lineTo((x + w - radiusBottomRight, y))
    path.arcTo((x + w, y), (x + w, y + radiusBottomRight), radiusBottomRight)
    path.lineTo((x + w, y + h - radiusTopRight))
    path.arcTo((x + w, y + h), (x + w - radiusTopRight, y + h), radiusTopRight)
    path.lineTo((x + radiusTopLeft, y + h))
    path.arcTo((x, y + h),  (x, y + h - radiusTopLeft), radiusTopLeft)
    path.lineTo((x, y + radiusBottomLeft))
    path.arcTo((x, y), (x + radiusBottomLeft, y), radiusBottomLeft)
    path.closePath()
    drawPath(path)

# draw a rounded rect
roundedRect(10, 10, 100, 100, 20, 20, 70, 90)