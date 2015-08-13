size(150,100)
# create seven pages
for i in range(7):

    # define the page size
    newPage(150, 100)

    # draw a random background
    fill(random(), random(), random())
    rect(10, 10, width()-20, height()-20)

    # set a fill
    fill(1)

    # draw some text
    text("Hello World %s!" % (i+1), (20, 40))

    # save only page 3 as pdf
    if i == 3:
        saveImage(["~/Desktop/firstImage.pdf"], multipage=False)

# save each page as a separate png
saveImage(["~/Desktop/firstImage.png"], multipage=True)
saveImage(["~/Desktop/firstImage.gif"])
