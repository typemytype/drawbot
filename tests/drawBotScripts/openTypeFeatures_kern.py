import drawBot

drawBot.newPage(130, 130)
drawBot.font("Times")
drawBot.text("ToTAVAT.", (10, 10))
drawBot.openTypeFeatures(kern=False)
drawBot.text("ToTAVAT.", (10, 30))
drawBot.openTypeFeatures(kern=True)
drawBot.text("ToTAVAT.", (10, 50))
# add tracking
drawBot.tracking(10)
drawBot.text("ToTAVAT.", (10, 70))
drawBot.openTypeFeatures(kern=False)
drawBot.text("ToTAVAT.", (10, 90))
drawBot.openTypeFeatures(kern=True)
drawBot.text("ToTAVAT.", (10, 110))
