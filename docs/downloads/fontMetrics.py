txt = "Hello World"
x, y = 10, 100

# set a font
font("Helvetica")
# set a font size
fontSize(100)
# draw the text
text(txt, (x, y))

# calculate the size of the text
textWidth, textHeight = textSize(txt)

# set a red stroke color
stroke(1, 0, 0)
# loop over all font metrics
for metric in (0, fontDescender(), fontAscender(), fontXHeight(), fontCapHeight()):
    # draw a red line with the size of the drawn text
    line((x, y+metric), (x+textWidth, y+metric))