import drawBot
drawBot.size(200, 200)
drawBot.stroke(0, 0, 1)
drawBot.strokeWidth(5)
with drawBot.savedState():
    drawBot.fill(1, 0, 0)
    drawBot.translate(100, 100)
    drawBot.rect(0, 0, 100, 100)
drawBot.rect(0, 0, 100, 100)
with drawBot.savedState():
    drawBot.fill(0, 1, 0)
    drawBot.translate(100, 0)
    drawBot.rect(0, 0, 100, 100)
drawBot.rect(0, 100, 100, 100)
