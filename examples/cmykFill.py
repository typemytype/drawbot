x, y = 0, 0
s = 100

# cyan
cmykFill(1, 0, 0, 0)
rect(x, y, s, s)
x += s

# magenta
cmykFill(0, 1, 0, 0)
rect(x, y, s, s)
x += s

# yellow
cmykFill(0, 0, 1, 0)
rect(x, y, s, s)
x += s

# black
cmykFill(0, 0, 0, 1)
rect(x, y, s, s)
