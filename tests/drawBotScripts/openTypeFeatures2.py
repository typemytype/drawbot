from drawBot import *

size(200, 200)

s = FormattedString()
s.font("HoeflerText-Regular")
s.fontSize(20)

s.append("Hoefler Fact #123\n")

s.openTypeFeatures(None)

s.openTypeFeatures(dlig=True)
s.append("Hoefler Fact #123\n")

s.openTypeFeatures(lnum=True)
s.append("Hoefler Fact #123\n")

s.openTypeFeatures(liga=False)
s.append("Hoefler Fact #123\n")

s.openTypeFeatures(liga=False, dlig=True, resetFeatures=True)
s.append("Hoefler Fact #123\n")

s.append("Hoefler Fact #123\n", openTypeFeatures=dict(liga=False, resetFeatures=True))

s.append("Hoefler Fact #123\n", openTypeFeatures=dict(dlig=True, resetFeatures=False))

textBox(s, (20, 0, 200, 190))
