# create an empty formatted string object
t = FormattedString()
# set a font
t.font("HoeflerText-Regular")
# set a font size
t.fontSize(60)
# add some text
t += "0123456789 Hello"
# enable some open type features
t.openTypeFeatures(smcp=True, lnum=True)
# add some text
t += " 0123456789 Hello"
# draw the formatted string
text(t, (10, 100))