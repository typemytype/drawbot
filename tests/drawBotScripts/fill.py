import drawBot
drawBot.size(100, 100)
drawBot.fill(.5, .5)
drawBot.oval(0, 0, 100, 100)
for x in range(10):
    for y in range(10):
        drawBot.fill(x / 10, 1 - y / 10, y / 10, y / 20 + .5)
        drawBot.rect(x*10, y*10, 10, 10)