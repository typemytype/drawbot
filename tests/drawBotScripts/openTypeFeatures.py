import drawBot

drawBot.size(200, 200)

# ['liga', 'dlig', 'tnum', 'pnum', 'titl', 'onum', 'lnum']

drawBot.font("HoeflerText-Regular")
drawBot.fontSize(20)
print(drawBot.listOpenTypeFeatures())

drawBot.text("Hoefler Fact #123", (20, 170))

drawBot.openTypeFeatures(None)

drawBot.openTypeFeatures(dlig=True)
drawBot.text("Hoefler Fact #123", (20, 140))

drawBot.openTypeFeatures(lnum=True)
drawBot.text("Hoefler Fact #123", (20, 110))

drawBot.openTypeFeatures(liga=False)
drawBot.text("Hoefler Fact #123", (20, 80))

drawBot.openTypeFeatures(liga=True, resetFeatures=False)
drawBot.text("Hoefler Fact #123", (20, 50))

drawBot.openTypeFeatures(liga=False, resetFeatures=True)
drawBot.text("Hoefler Fact #123", (20, 20))
