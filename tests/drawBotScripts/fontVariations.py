import drawBot

drawBot.newPage(1000, 600)
# pick a font
drawBot.font("Skia")
# pick a font size
drawBot.fontSize(200)
# list all axis from the current font
variations = drawBot.listFontVariations()
for axisTag in sorted(variations):
    data = variations[axisTag]
    # round values to avoid small per-OS float differences
    data["defaultValue"] = round(float(data["defaultValue"]), 3)
    data["minValue"] = round(float(data["minValue"]), 3)
    data["maxValue"] = round(float(data["maxValue"]), 3)
    data["name"] = str(data["name"])
    print(axisTag, [(k, data[k]) for k in sorted(data)])
# pick a variation from the current font
drawBot.fontVariations(wght=0.6)
# draw text!!
drawBot.text("Hello Q", (100, 40))
# pick a variation from the current font
drawBot.fontVariations(wght=3, wdth=1.2)
# draw text!!
drawBot.text("Hello Q", (100, 220))
# reset defaults
drawBot.fontVariations(resetVariations=True)
drawBot.text("Hello Q", (100, 420))

drawBot.save()
