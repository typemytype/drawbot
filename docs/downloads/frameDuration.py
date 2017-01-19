# setting some variables
# size of the pages / frames
w, h = 200, 200
# frame per seconds
fps = 30
# duration of the movie
seconds = 3
# calculate the lenght of a single frame
duration = 1 / fps
# calculate the amount of frames needed
totalFrames = seconds * fps

# title page
newPage(w, h)
# set frame duration to 1 second
frameDuration(1)
# pick a font and font size
font("Helvetica", 40)
# draw the title text in a box
textBox("Rotated square", (0, 0, w, h * .8), align="center")

# loop over the amount of frames needed
for i in range(totalFrames):
    # create a new page
    newPage(w, h)
    # set the frame duration
    frameDuration(duration)
    # set a fill color
    fill(1, 0, 0)
    # translate to the center of the page
    translate(w / 2, h / 2)
    # rotate around the center
    rotate(i*10)
    # draw the rect
    rect(-50, -50, 50, 50)

# save the image as a mov on the desktop
saveImage('~/Desktop/frameDuration.mov')