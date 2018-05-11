import drawBot
drawBot.size(200, 200)

drawBot.newPath()
drawBot.moveTo((20, 20))
drawBot.lineTo((20, 100))
drawBot.lineTo((100, 100))
drawBot.lineTo((100, 180))
drawBot.curveTo((150, 180), (180, 150), (180, 100))
drawBot.lineTo((180, 50))
drawBot.qCurveTo((180, 20), (150, 20))

drawBot.fill(1, 0, 0)
drawBot.stroke(0)
drawBot.strokeWidth(10)
drawBot.drawPath()

drawBot.closePath()

drawBot.fill(None)
drawBot.stroke(1)
drawBot.translate(40, 15)
drawBot.scale(0.7)
drawBot.lineCap("round")
drawBot.lineJoin("round")

drawBot.drawPath()
