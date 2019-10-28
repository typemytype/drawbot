import drawBot
drawBot.size(200, 200)
drawBot.fontSize(20)
fs = drawBot.FormattedString("foo bar", fontSize=20)
drawBot.text(fs, (drawBot.width()*.5, 100), align="right")
drawBot.text(fs, (drawBot.width()*.5, 120), align="center")
drawBot.text(fs, (drawBot.width()*.5, 140), align="left")
