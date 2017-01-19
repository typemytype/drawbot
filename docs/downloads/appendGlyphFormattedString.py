# create an empty formatted string object
t = FormattedString()
# set a font
t.font("Menlo-Regular")
# set a font size
t.fontSize(60)
# add some glyphs
t.appendGlyph("Eng", "Eng.alt")
# draw the formatted string
text(t, (10, 100))