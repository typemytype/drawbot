from drawBot import *

size(200, 200)

s = FormattedString()

s.font("Skia")
s.fontSize(30)
s.lineHeight(30)
s.fontVariations(None)

s.append("Hello Q\n")
s.fontVariations(wght=0.6)
s.append("Hello Q\n")
s.fontVariations(wght=2.4)
s.append("Hello Q\n")

s.append("Hello Q\n", fontVariations=dict(wdth=1.29))

s.append("Hello Q\n", fontVariations=dict(wdth=0.6, resetVariations=True))

s.fontVariations(wght=2.8, resetVariations=False)
s.append("Hello Q\n")

textBox(s, (10, 0, 190, 193))
