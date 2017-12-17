import drawBot
drawBot.newDrawing()
drawBot.size(600, 100)
p1 = drawBot.BezierPath()
p1.oval(5, 5, 70, 70)
p2 = drawBot.BezierPath()
p2.rect(25, 25, 70, 70)
drawBot.fill(0, 0.3)
drawBot.stroke(0)

drawBot.drawPath(p1)
drawBot.drawPath(p2)

pUnion = p1.union(p2)
pIntersection = p1.intersection(p2)
pXor = p1.xor(p2)
pDiff1 = p1.difference(p2)
pDiff2 = p2.difference(p1)

for p in [pUnion, pIntersection, pXor, pDiff1, pDiff2]:
    drawBot.translate(100, 0)
    drawBot.drawPath(p)
