import drawBot
drawBot.newDrawing()
drawBot.size(200, 200)

def rotateScale(r, s, center):
    drawBot.rotate(r, center=center)
    drawBot.scale(s, center=center)


testData = [
    ((25, 25, 50, 50), drawBot.rotate, (20,), (25, 25)),
    ((125, 25, 50, 50), drawBot.skew, (10, 10), (175, 25)),
    ((25, 125, 50, 50), drawBot.scale, (1.2, 1.4), (25, 175)),
    ((125, 125, 50, 50), rotateScale, (20, 0.8), (175, 175)),
]

for r, op, args, center in testData:
    drawBot.fill(0)
    drawBot.rect(*r)
    with drawBot.savedState():
        drawBot.fill(1, 0, 0, 0.5)
        op(*args, center=center)
        drawBot.rect(*r)
