# set the canvas size
size(150, 100)

# draw a background
rect(10, 10, width()-20, height()-20)

# set a fill
fill(1)
# draw some text
text("Hello World!", (20, 40))
# save it as a png and pdf on the current users desktop
saveImage(["~/Desktop/firstImage.png", "~/Desktop/firstImage.pdf"])