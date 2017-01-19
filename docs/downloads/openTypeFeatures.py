# set a font
font("ACaslonPro-Regular")
# set the font size
fontSize(50)
# draw a string
text("aa1465", (100, 200))
# enable some OpenType features
openTypeFeatures(lnum=True, smcp=True)
# draw the same string
text("aa1465", (100, 100))