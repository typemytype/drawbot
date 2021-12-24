import pathlib
import drawBot
drawBot.size(500, 500)
imagePath = "../data/drawBot.pdf"
w, h = drawBot.imageSize(imagePath)
drawBot.save()
drawBot.scale(250 / w)
drawBot.image(imagePath, (0, 0))
drawBot.restore()

imagePath = "../data/drawBot.png"
w, h = drawBot.imageSize(imagePath)
drawBot.save()
drawBot.scale(250 / w)
drawBot.image(imagePath, (w, 0))
drawBot.restore()

imagePath = "../data/drawBot.jpg"
w, h = drawBot.imageSize(imagePath)
drawBot.save()
drawBot.scale(250 / w)
drawBot.image(imagePath, (0, h))
drawBot.restore()

imagePath = "../data/drawBot.bmp"
w, h = drawBot.imageSize(imagePath)
drawBot.save()
drawBot.scale(250 / w)
drawBot.image(pathlib.Path(imagePath), (w, h))  # verify that pathlib.Path objects work
drawBot.restore()
