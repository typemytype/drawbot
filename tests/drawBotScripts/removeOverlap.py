import drawBot

drawBot.newDrawing()
drawBot.size(200, 100)
p = drawBot.BezierPath()
p.oval(5, 5, 70, 70)
p.rect(25, 25, 70, 70)
drawBot.fill(0, 0.3)
drawBot.stroke(0)
drawBot.drawPath(p)
p.removeOverlap()
drawBot.translate(100, 0)
drawBot.drawPath(p)
