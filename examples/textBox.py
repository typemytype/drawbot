x, y, w, h = 100, 100, 256, 174

fill(1, 0, 0)
rect(x, y, w, h)
fill(1)
fontSize(50)
overflow = textBox("hallo, this text is a bit to long",
                (x, y, w, h), align="center")
print overflow