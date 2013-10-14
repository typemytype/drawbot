t = """DrawBot is a powerful, free application for MacOSX that invites you to write simple Python scripts to generate two-dimensional graphics. The builtin graphics primitives support rectangles, ovals, (bezier) paths, polygons, text objects and transparency. 
DrawBot is an ideal tool to teach the basics of programming. Students get colorful graphic treats while getting familiar with variables, conditional statements, functions and what have you. Results can be saved in a selection of different file formats, including as high resolution, scaleable PDF. 
DrawBot has proven itself as part of the curriculum at selected courses at the Royal Academy in The Hague."""


# setting some variables 
# setting the size
x, y, w, h = 10, 10, 480, 480

# setting the color change over different frames
coloradd = .1

# setting the start background color only red and blue
r = .3
b = 1

# start a loop and run as long there is t variable has some text
while len(t):
    # create a new page
    newPage(500, 500)
    # set a frame duration
    frameDuration(3)
    # set the background fill
    fill(r, 0, b)
    # draw the background
    rect(x, y, w, h)
    # set a fill color    
    fill(0)
    # set a font with a size
    font("DrawBot-Bold", randint(50, 100))
    # pick some random colors
    rr = random()
    gg = random()
    bb = random()
    # set a gradient as fill
    radialGradient((250, 250), (250, 250), [(rr, gg, bb), (1-rr, 1-gg, 1-bb)], startRadius=0, endRadius=250)
    
    # draw the text in a box with the gradient fill
    t = textBox(t, (x, y, w, h))
    
    # setting the color for the next frame
    r += coloradd
    b -= coloradd
    
    # set a font
    font("DrawBot-Bold", 20)
    # get the page count text size as a (width, height) tuple
    tw, th = textSize("%s" % pageCount())
    # draw the text
    textBox("%s" % pageCount(), (10, 10, 480, th), align="center")

saveImage("~/Desktop/drawbot.mov")

