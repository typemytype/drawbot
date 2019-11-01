import drawBot
f = drawBot.FormattedString()
f.fontSize(40)
f.font("Helvetica")
f.align("left")
f.append("left\n")
f.align("center")
f.append("center\n")
f.font("Times")
f.align("right")
f.append("right\n")

_, height = f.size()
x, y = drawBot.width() * .25, 200

with drawBot.savedState():
    drawBot.stroke(0)
    drawBot.line((x, 0), (x, 1000))


drawBot.text(f, (x, y))
y += height
drawBot.text(f, (x, y), align="left")
y += height
drawBot.text(f, (x, y), align="center")
y += height
drawBot.text(f, (x, y), align="right")

x, y = drawBot.width() * .75, 200
with drawBot.savedState():
    drawBot.stroke(0)
    drawBot.line((x, 0), (x, 1000))

b = drawBot.BezierPath()
b.text(f)
b.text(f, offset=(0, height), align="left")
b.text(f, offset=(0, height * 2), align="center")
b.text(f, offset=(0, height * 3), align="right")
drawBot.translate(x, y)
drawBot.fill(1, 0, 0)
drawBot.drawPath(b)
