import drawBot
drawBot.newPage(100, 70)
drawBot.font("Times")
drawBot.text("ToTAVAT.", (10, 10))
drawBot.openTypeFeatures(kern=False)
drawBot.text("ToTAVAT.", (10, 30))
drawBot.openTypeFeatures(kern=True)
drawBot.text("ToTAVAT.", (10, 50))