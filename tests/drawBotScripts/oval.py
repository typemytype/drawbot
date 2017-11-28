import drawBot
drawBot.size(200, 200)
for i in range(14):
    f = i / 14.0
    drawBot.fill(1-f, 1 - f, 0)
    drawBot.oval(10, 10, 50, 50)
    drawBot.translate(10, 10)