# https://github.com/typemytype/drawbot/issues/402
import drawBot
drawBot.size(640, 160)

fs = drawBot.FormattedString()
fs.font("Skia")
fs.fontSize(200)
fs.fontVariations(wght=1)
fs += "&"
fs.appendGlyph("ampersand")
fs.fontVariations(wght=2)
fs.appendGlyph("ampersand")
fs += "&"

drawBot.text(fs, (10, 10))
