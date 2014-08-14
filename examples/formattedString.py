
# create a formatted string
txt = FormattedString()

# adding some text with some formatting
txt.append("hello", font="Helvetica", fontSize=100, fill=(1, 0, 0))
# adding more text
txt.append("world", font="Times-Italic", fontSize=50, fill=(0, 1, 0))

# setting a font
txt.font("Helvetica-Bold")
txt.fontSize(75)
txt += "hello again"

# drawing the formatted string
text(txt, (10, 10))


# create a formatted string
txt = FormattedString()

# adding some text with some formatting
txt.append("hello", font="Hoefler Text", fontSize=50)
# adding more text with an
txt.append("world", font="Hoefler Text", fontSize=50, openTypeFeatures=dict(smcp=True))

text(txt, (10, 110))