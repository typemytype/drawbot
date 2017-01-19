x, y = 20, 20
lines = 20

colorStep = 1.00 / lines

strokeWidth(10)

for i in range(lines):
    cmykStroke(0, i * colorStep, 1, 0)
    line((x, y), (x, y + 200))
    translate(12, 0)