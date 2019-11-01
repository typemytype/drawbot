Quick Reference
===============

.. downloadcode:: quickReference.py

    # DrawBot reference

    # set a size for the canvas
    size(500, 500)

    # using the functions width, height and pageCount
    print("width:", width())
    print("height:", height())

    print("pageCount:", pageCount())

    # simple shapes

    # draw rect x, y, width, height
    rect(10, 10, 100, 100)

    # draw oval x, y, width, height
    oval(10, 120, 100, 100)
    oval(120, 120, 100, 100)

    # draw polygon
    polygon((10, 250), (100, 250), (100, 400), (50, 300), close=False)

    # create path
    newPath()
    # move to point
    moveTo((300, 100))
    lineTo((400, 100))

    # first control point (x1, y1)
    # second control point (x2, y2)
    # end point (x3, y3)
    curveTo((450, 150), (450, 250), (400, 300))
    lineTo((300, 300))
    # close the path
    closePath()
    # draw the path
    drawPath()

    newPage()
    # image: path, (x, y), alpha
    image("https://d1sz9tkli0lfjq.cloudfront.net/items/1T3x1y372J371p0v1F2Z/drawBot.jpg", (10, 10), .5)

    newPage()
    print("pageCount:", pageCount())
    # colors
    # fill(r, g, b)
    # fill(r, g, b, alpha)
    # fill(grayvalue)
    # fill(grayvalue, alpha)
    # fill(None)
    fill(.5)
    rect(10, 10, 100, 100)

    fill(1, 0, 0)
    rect(10, 120, 100, 100)

    fill(0, 1, 0, .5)
    oval(50, 50, 100, 100)

    fill(None)

    # stroke(r, g, b)
    # stroke(r, g, b, alpha)
    # stroke(grayvalue)
    # stroke(grayvalue, alpha)
    # stroke(None)
    strokeWidth(8)
    stroke(.8)
    rect(200, 10, 100, 100)

    stroke(.1, .1, .8)
    rect(200, 120, 100, 100)

    strokeWidth(20)
    stroke(1, 0, 1, .5)
    oval(250, 50, 100, 100)


    newPage()
    # stroke attributes

    print("pageCount:", pageCount())
    fill(None)
    stroke(0)
    strokeWidth(8)

    lineCap("square")
    lineJoin("miter")
    miterLimit(5)
    polygon((10, 10), (10, 400), (50, 350), close=False)

    lineCap("round")
    lineJoin("round")
    polygon((110, 10), (110, 400), (150, 350), close=False)

    lineCap("butt")
    lineJoin("bevel")
    polygon((210, 10), (210, 400), (250, 350), close=False)

    lineDash(10, 10, 2, 5)
    polygon((310, 10), (310, 400), (350, 350), close=False)

    newPage()
    print("pageCount:", pageCount())

    text("Hello World", (10, 10))

    fontSize(100)
    fill(1, 0, 0)
    stroke(0)
    strokeWidth(5)
    text("Hello World", (10, 20))

    font("Times-Italic", 25)
    fill(0, .5, 1)
    stroke(None)
    textBox("Hello World " * 100, (10, 150, 300, 300))


    print("textSize:", textSize("Hallo"))

    newPage()
    # canvas transformations
    print("pageCount:", pageCount())

    fill(None)
    stroke(0)
    strokeWidth(3)
    save()
    rect(10, 10, 100, 100)


    scale(2)
    rect(10, 10, 100, 100)
    restore()

    save()
    rotate(30)
    rect(10, 10, 100, 100)
    restore()

    save()
    skew(30)
    rect(10, 10, 100, 100)
    restore()

    newPage()
    print("pageCount:", pageCount())

    #    c m y k alpha
    cmykFill(0, 1, 0, 0)
    rect(10, 10, 100, 100)

    strokeWidth(5)
    cmykFill(None)
    cmykStroke(0, 1, 1, 0)
    rect(10, 110, 100, 100)

    cmykLinearGradient((10, 210), (10, 310), ([1, 1, 1, 1], [0, 1, 1, 0]))
    rect(10, 210, 100, 100)

    cmykStroke(None)

    cmykRadialGradient((50, 410), (50, 410), ([1, 0, 1, 0], [1, 1, 0, 0], [0, 1, 1, 0]), startRadius=0, endRadius=300)
    rect(10, 310, 100, 150)

    cmykShadow((10, 10), 20, (0, 1, 1, 0))
    oval(130, 310, 300, 150)

    newPage()
    print("pageCount:", pageCount())

    fill(1, 0, 1)
    linearGradient((10, 10), (200, 20), ([1, 1, 0], [0, 1, 1]))

    rect(10, 10, 200, 200)

    radialGradient((50, 410), (50, 410), ([1, 0, 1], [1, 1, 0], [0, 1, 1]), startRadius=0, endRadius=300)
    rect(10, 310, 100, 150)

    shadow((10, 10), 20, (1, 0, 0))
    oval(130, 310, 300, 150)

    newPage()

    save()

    path = BezierPath()
    path.oval(20, 20, 300, 100)
    clipPath(path)

    fill(1, 0, 0, .3)
    rect(10, 10, 100, 100)

    fontSize(30)
    text("Hello World", (50, 80))

    restore()

    oval(200, 20, 50, 50)

    saveImage(u"~/Desktop/drawBotTest.pdf")
    saveImage(u"~/Desktop/drawBotTest.png")
    saveImage(u"~/Desktop/drawBotTest.svg")
    saveImage(u"~/Desktop/drawBotTest.mp4")

    print("Done")
