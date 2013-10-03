size(512, 512)

# Draw the D
p = BezierPath()
p.moveTo((36, 234))
p.lineTo((46, 38))
p.curveTo((46, 38), (242, -22), (242, 134))
p.curveTo((242, 270), (106, 250), (36, 234))
p.closePath()
p.moveTo((113, 175))
p.curveTo((136, 180), (162, 178), (162, 136))
p.curveTo((162, 87), (116, 97), (116, 97))
p.closePath()

def drawIcon():    
    save()
    skew(2, -2)
    scale(2)
    translate(5, 0)
    
    save()
    translate(-10, -25)
    skew(-5, 5)
    fill(0, 0, 0, .5)
    drawPath(p)
    restore()


    save()
    clipPath(p)
    
    r, g, b = 1, .5, 0
    fill(r, g, b)
    rect(0, 0, width(), height())

    for i in range(20):
        r, g, b = 1, 1, 1
        fill(random(), random(), random(), random() * 0.8)
        
        newPath()
        x, y = 400, 400
        moveTo((random()*x, random()*y))
        x, y = 200, 200
        i = 100
        curveTo((random()*x+i, random()*y+i), (random()*x+i, random()*y+i), (random()*x+i, random()*y+i))
        curveTo((random()*x+i, random()*y+i), (random()*x+i, random()*y+i), (random()*x+i, random()*y+i))
        curveTo((random()*x+i, random()*y+i), (random()*x+i, random()*y+i), (random()*x+i, random()*y+i))
        closePath()
        drawPath()
    
    
    save()
    loop = randint(3, 9)
    for i in range(loop):
        s = randint(30, 55)
        if choice([True, False]):
            fill(1, 0, 0, 0.5)
        else:
            fill(1, 0, 0, 0)
            strokeWidth(2)
            stroke(1, 0, 0, 0.5)
        oval(random()*200, random()*200, s, s)
    restore()


    save()
    translate(-10, -10)
    fill(None)
    stroke(0, 0, 0, 0.5)
    strokeWidth(25)
    drawPath(p)
    restore()

    restore()

    save()
    fill(None)
    stroke(1, 1, 1)
    strokeWidth(8)
    drawPath(p)
    restore()
    
    save()
    loop = randint(3, 9)
    for a02loop in range(loop):
        s = randint(25, 50)
        strokeWidth(2)
        stroke(1, 1, 1)
        if choice([True, False]):
            fill(1, 1, 1, 0.5)
        else:
            fill(None) 
        oval(random()*200, random()*200, s, s)
    restore()
    
    restore()

drawIcon()
saveImage(u"~/Desktop/drawBotIcon.svg")