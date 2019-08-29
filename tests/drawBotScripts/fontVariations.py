from drawBot import *

size(200, 200)

font("Skia")
fontSize(30)

fontVariations(None)

variations = listFontVariations()
for axisTag in sorted(variations):
    data = variations[axisTag]
    # we're rounding the values so we don't trip over small differences between OSes
    data['defaultValue'] = round(data['defaultValue'], 3)
    data['minValue'] = round(data['minValue'], 3)
    data['maxValue'] = round(data['maxValue'], 3)
    data['name'] = str(data['name'])
    print(axisTag, [(k, data[k]) for k in sorted(data)])

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
