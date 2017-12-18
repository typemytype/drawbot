import drawBot
drawBot.size(500, 500)
imagePath = "../data/drawBot.png"
w, h = drawBot.imageSize(imagePath)
drawBot.scale(250 / w)
drawBot.image(imagePath, (0, 0))
drawBot.image(imagePath, (w, 0), alpha=0.5)
drawBot.image(imagePath, (0, h), alpha=0.25)
drawBot.image(imagePath, (w, h), alpha=0.75)
