w, h = 150, 150
message = bytes('https://drawbot.com', 'latin-1')


newPage(w + 20, h + 20)
img = ImageObject()
img.aztecCodeGenerator((w, h), message)
image(img, (10, 10))

newPage(w + 20, h + 20)
img = ImageObject()
img.QRCodeGenerator((w, h), message, 'H')
image(img, (10, 10))

newPage(w + 20, h + 20)
img = ImageObject()
img.code128BarcodeGenerator((w, h), message, 0)
image(img, (10, 10))

newPage(w + 20, h + 20)
img = ImageObject()
img.checkerboardGenerator((w, h), width=20)
image(img, (10, 10))


newPage()
img = ImageObject()
img.constantColorGenerator((w, h), (1, 1, 0, 1))
image(img, (10, 10))


newPage()
img = ImageObject()
img.lenticularHaloGenerator((w, h))
image(img, (10, 10))

newPage()
img = ImageObject()
img.PDF417BarcodeGenerator((w, h), message)
image(img, (10, 10))

newPage()
img = ImageObject()
img.randomGenerator((w, h))
image(img, (10, 10))

newPage()
img = ImageObject()
img.starShineGenerator((w, h), center=(w/2, h/2), color=(1, 0, 0, 1), radius=20)
image(img, (10, 10))

newPage()
img = ImageObject()
img.stripesGenerator((w, h), width=10)
image(img, (10, 10))

newPage()
img = ImageObject()
img.sunbeamsGenerator((w, h), center=(w/2, h/2))
image(img, (10, 10))
