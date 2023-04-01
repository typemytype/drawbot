import os
import drawBot
drawBot.size(50, 50)
characters = "Aa今"
glyphNames = ["A", "a", "zzz"]
for fontName in ["Times", "../data/MutatorSans.ttf"]:
    print(fontName)
    print(drawBot.font(fontName))
    drawBot.fontSize(50)
    for char in characters:
        print(drawBot.fontContainsCharacters(char))
    for glyphName in glyphNames:
        print(drawBot.fontContainsGlyph(glyphName))
    print(os.path.basename(drawBot.fontFilePath()))
    print(drawBot.listFontGlyphNames()[:6])
    print(drawBot.fontAscender())
    print(drawBot.fontDescender())
    print(drawBot.fontXHeight())
    print(drawBot.fontCapHeight())
    print(drawBot.fontLeading())
    print(drawBot.fontLineHeight())
    print()

# https://github.com/typemytype/drawbot/issues/524
print(drawBot.font("Apple Color Emoji"))
print(drawBot.fontContainsCharacters(chr(0x1F004)))
print()

for i in range(4):
    print(drawBot.font("../data/MutatorSans.ttc", fontNumber=i))
    print(os.path.basename(drawBot.fontFilePath()), drawBot.fontFileFontNumber())
    assert drawBot.fontFileFontNumber() == i

print()
for fontName in ["Courier", "Courier-Bold", "Courier-Oblique"]:
    drawBot.font(fontName)
    print(fontName, os.path.basename(drawBot.fontFilePath()), drawBot.fontFileFontNumber())
