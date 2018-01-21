from drawBot import *

size(200, 200)

# ['liga', 'dlig', 'tnum', 'pnum', 'titl', 'onum', 'lnum']

font("HoeflerText-Regular")
fontSize(20)
print(listOpenTypeFeatures())

text("Hoefler Fact #123", (20, 170))

openTypeFeatures(None)

openTypeFeatures(dlig=True)
text("Hoefler Fact #123", (20, 140))

openTypeFeatures(lnum=True)
text("Hoefler Fact #123", (20, 110))

openTypeFeatures(liga=False)
text("Hoefler Fact #123", (20, 80))

openTypeFeatures(liga=True, resetFeatures=False)
text("Hoefler Fact #123", (20, 50))

openTypeFeatures(liga=False, resetFeatures=True)
text("Hoefler Fact #123", (20, 20))
