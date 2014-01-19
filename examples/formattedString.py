
# create a formatted string
txt = FormattedString()

# adding some text with some formatting
txt.append("hello", font="Helvetica", fontSize=100, fill=(1, 0, 0))
# adding more text
txt.append("world", font="Times-Italic", fontSize=50, fill=(0, 1, 0))

# drawing the formatted string
text(txt, (10, 10))