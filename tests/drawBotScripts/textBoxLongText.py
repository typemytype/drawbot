# See bug: https://github.com/typemytype/drawbot/issues/585
import drawBot

drawBot.size(200, 200)
box = (10, 10, 180, 180)
drawBot.fontSize(18)
drawBot.font("Hoefler Text")
drawBot.textBox("fifl" * 3000, box)
