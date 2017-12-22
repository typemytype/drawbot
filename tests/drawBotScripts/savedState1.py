import drawBot
drawBot.size(300, 300)
with drawBot.savedState():
    drawBot.fill(1, 0, 0)
    drawBot.translate(150, 150)
    drawBot.rect(0, 0, 100, 100)
    with drawBot.savedState():
        drawBot.rotate(45)
        drawBot.fill(0, 1, 0)
        drawBot.rect(0, 0, 100, 100)
drawBot.rect(0, 0, 100, 100)
