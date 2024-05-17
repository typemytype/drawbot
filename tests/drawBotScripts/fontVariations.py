import drawBot

drawBot.size(200, 200)

drawBot.font("Skia")
drawBot.fontSize(30)

drawBot.fontVariations(None)

variations = drawBot.listFontVariations()
for axisTag in sorted(variations):
    data = variations[axisTag]
    # we're rounding the values so we don't trip over small differences between OSes
    data['defaultValue'] = round(float(data['defaultValue']), 3) # we need floats to make sure that 1 becomes 1.0
    data['minValue'] = round(float(data['minValue']), 3)
    data['maxValue'] = round(float(data['maxValue']), 3)
    data['name'] = str(data['name'])
    print(axisTag, [(k, data[k]) for k in sorted(data)])

drawBot.text("Hello Q", (20, 170))
drawBot.fontVariations(wght=0.6)
drawBot.text("Hello Q", (20, 140))
drawBot.fontVariations(wght=2.4)
drawBot.text("Hello Q", (20, 110))

drawBot.fontVariations(wdth=1.29)
drawBot.text("Hello Q", (20, 80))

drawBot.fontVariations(wdth=0.6, resetVariations=True)
drawBot.text("Hello Q", (20, 50))

drawBot.fontVariations(wght=2.8, resetVariations=False)
drawBot.text("Hello Q", (20, 20))
