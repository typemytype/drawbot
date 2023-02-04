# https://github.com/typemytype/drawbot/issues/427
import drawBot
drawBot.size(200, 200)

fs = drawBot.FormattedString()
fs.font("Lucida Grande")
fs.fontSize(50)
fs.appendGlyph("H")
fs.appendGlyph("i")
drawBot.text(fs, (30, 110))

fs = drawBot.FormattedString()
fs.font("Lucida Grande")
fs.fontSize(50)
fs.tracking(10)
fs.appendGlyph("H")
fs.appendGlyph("i")
drawBot.text(fs, (30, 50))
