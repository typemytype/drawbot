import drawBot
drawBot.newDrawing()
drawBot.size(200, 200)

testData = [
    ((25, 25, 50, 50), "rotate", (20,), (25, 25)),
    ((125, 25, 50, 50), "skew", (10, 10), (175, 25)),
    ((25, 125, 50, 50), "scale", (1.2, 1.4), (25, 175)),
]

for r, op, args, center in testData:
    drawBot.fill(0)
    bez = drawBot.BezierPath()
    bez.rect(*r)
    drawBot.drawPath(bez)
    with drawBot.savedState():
        drawBot.fill(1, 0, 0, 0.5)
        bez = drawBot.BezierPath()
        bez.rect(*r)
        getattr(bez, op)(*args, center=center)
        drawBot.drawPath(bez)
