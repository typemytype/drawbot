# loop over a range of 100
for i in range(100):
    # for each loop create a new path
    newPage(500, 500)
    # set a random fill color
    fill(random(), random(), random())
    # draw a rect with the size of the page
    rect(0, 0, width(), height())