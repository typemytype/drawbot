import drawBot
drawBot.newDrawing()
drawBot.newPage(40, 40)
path = drawBot.BezierPath()
path.rect(10, 10, 20, 20)

dashedPath = path.dashStroke(5, 5)

drawBot.fill(None)
drawBot.stroke(0)
drawBot.drawPath(dashedPath)