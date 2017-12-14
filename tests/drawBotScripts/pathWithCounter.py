import drawBot
drawBot.size(200, 200)

drawBot.newPath()
drawBot.moveTo((20, 20))
drawBot.lineTo((20, 100))
drawBot.lineTo((100, 100))
drawBot.lineTo((100, 180))
drawBot.curveTo((150, 180), (180, 150), (180, 100))
drawBot.lineTo((180, 20))
drawBot.closePath()

drawBot.moveTo((40, 40))
drawBot.lineTo((160, 40))
drawBot.curveTo((160, 65), (145, 80), (120, 80))
drawBot.lineTo((40, 80))
drawBot.closePath()

drawBot.fill(0.5, 0, 0)
drawBot.stroke(None)
drawBot.strokeWidth(10)
drawBot.drawPath()
