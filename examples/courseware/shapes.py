# draw a rectangle
# rect(x, y, width, height)
rect(20, 50, 100, 200)

rect(130, 50, 100, 200)

oval(240, 50, 100, 200)

oval(20, 250, 100, 100)

oval(130, 250, 100, 100)

rect(240, 250, 100, 100)

for x in range(20, 300, 50):
    rect(x, 370, 40, 40)

for x in range(20, 300, 50):
    if random() > 0.5:
        rect(x, 420, 40, 40)
    else:
        oval(x, 420, 40, 40)
