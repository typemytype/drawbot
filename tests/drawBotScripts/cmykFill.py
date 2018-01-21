import drawBot
drawBot.size(100, 100)
for x in range(10):
    for y in range(10):
        drawBot.cmykFill(x / 10, 1 - y / 10, y / 10, 0)
        drawBot.rect(x*10, y*10, 5, 10)
        drawBot.cmykFill(x / 10, 1 - y / 10, y / 10, 0.2)
        drawBot.rect(x*10 + 5, y*10, 5, 5)
        drawBot.cmykFill(x / 10, 1 - y / 10, y / 10, 0, 0.55)
        drawBot.rect(x*10 + 5, y*10 + 5, 5, 5)
