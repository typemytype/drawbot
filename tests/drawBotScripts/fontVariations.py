from __future__ import print_function
from drawBot import *

size(200, 200)

font("Skia")
fontSize(30)

fontVariations(None)

variations = listFontVariations()
for axisTag in sorted(variations):
    data = variations[axisTag]
    print(axisTag, [(k, str(data[k])) for k in sorted(data)])

text("Hello Q", (20, 170))
fontVariations(wght=0.6)
text("Hello Q", (20, 140))
fontVariations(wght=2.4)
text("Hello Q", (20, 110))

fontVariations(wdth=1.29)
text("Hello Q", (20, 80))

fontVariations(wdth=0.6, resetVariations=True)
text("Hello Q", (20, 50))

fontVariations(wght=2.8, resetVariations=False)
text("Hello Q", (20, 20))
