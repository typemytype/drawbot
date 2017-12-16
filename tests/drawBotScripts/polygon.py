import drawBot
drawBot.size(200, 200)
drawBot.stroke(0)
drawBot.strokeWidth(10)
drawBot.fill(1, 0.3, 0)
drawBot.polygon((40, 40), (40, 160))
drawBot.polygon((60, 40), (60, 160), (130, 160))
drawBot.polygon((100, 40), (160, 160), (160, 40), close=False)
