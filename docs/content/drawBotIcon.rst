DrawBot Icon
============

The making of (by Andy Clymer)

.. downloadcode:: drawBotIcon.py

    from ufoLib.glifLib import readGlyphFromString
    from fontTools.pens.cocoaPen import CocoaPen
    from fontParts.fontshell.glyph import RGlyph
    import random
    import os

    tryAndError = False
    drawPencil = True
    drawBubbles = True

    # Big pencil for the file icon?
    # (and then only save the first frame)
    bigPencil = False

    # Left handed?
    leftHand = True

    # Reduced color palette for file icon?
    reducedPalette = False

    folderPath = os.path.split(__file__)[0]
    savePath = os.path.join(folderPath, "icon.gif")
    singleFileSavePath = os.path.join(folderPath, "icon_%s.png")
    #savePath = os.path.join(folderPath, "icon.png")


    lightOrange = [1, 0.75, 0, 1]
    orange = [1, 0.5, 0, 1]
    redOrange = [1, 0.25, 0.1, 1]
    darkOrange = [0.3, 0.15, 0, .4]
    pinkish = [1, 0.5, 0.6, 1]
    magenta = [0.9, 0.1, 0.5, 1]
    purple = [0.7, 0.1, 0.8, 1]
    darkPurple = [0.5, 0, 0.5]
    brightPurple = [1, 0.1, 1, 1]
    gray = [0.8, 0.8, 0.8, 1]
    white = [1, 1, 1, 1]


    # Glif string
    iconGlifString = b"""<?xml version="1.0" encoding="UTF-8"?>
    <glyph name="A" format="1">
      <advance width="0"/>
      <outline>
        <contour>
          <point x="95" y="407" type="line"/>
          <point x="328" y="442"/>
          <point x="422" y="391"/>
          <point x="422" y="258" type="curve" smooth="yes"/>
          <point x="422" y="124"/>
          <point x="328" y="73"/>
          <point x="95" y="108" type="curve"/>
        </contour>
        <contour>
          <point x="218" y="305" type="curve"/>
          <point x="218" y="210" type="line"/>
          <point x="275" y="206"/>
          <point x="300" y="221"/>
          <point x="300" y="258" type="curve" smooth="yes"/>
          <point x="300" y="295"/>
          <point x="275" y="310"/>
        </contour>
      </outline>
    </glyph>
    """

    # Read the string into a glyph object
    iconGlyph = RGlyph()
    pen = iconGlyph.getPointPen()
    readGlyphFromString(iconGlifString, glyphObject=iconGlyph, pointPen=pen)

    iconGlyph.scaleBy((1.12, 1.2))

    # Fetch the path of the glyph as a NSBezierPath
    pen = CocoaPen(None)
    iconGlyph.draw(pen)
    iconPath = pen.path
    # ...and then convert it to a DrawBot BezierPath
    iconPath = BezierPath(iconPath)

    # Remove the inside contour of the glyph, and read another path
    iconGlyph.removeContour(1)
    # Fetch the path of the glyph as a NSBezierPath
    pen = CocoaPen(None)
    iconGlyph.draw(pen)
    iconOutsidePath = pen.path
    # ...and then convert it to a DrawBot BezierPath
    iconOutsidePath = BezierPath(iconOutsidePath)



    """ Helper functions """

    def interpolate(f, a, b):
        v = (a + (b - a) * f)
        return v

    def interpolateColor(f, color0=None, color1=None):
        # Default the two colors to pinkish orange and magenta:
        if not color0:
            if reducedPalette:
                color0 = white
            else: color0 = lightOrange
        if not color1:
            if reducedPalette:
                color1 = orange
            else: color1 = orange
        newColor = []
        # Interpolate
        for i in range(4):
            newColor.append(interpolate(f, color0[i], color1[i]))
        return tuple(newColor)


    def drawBubble(size, phase):
        # Shift the phase
        if phase > 1:
            phase = phase - 1
        # Scale the phase, so that it doesn't happen all the time
        phase *= 3
        # Draw if it's durring the current phase
        if phase < 1:
            fill(1, 1, 1, 1-phase)
            stroke(1, 1, 1, 1)
            strokeWidth(10 * (1-phase))
            phaseSize = phase*size
            oval(-0.5*phaseSize, -0.5*phaseSize, phaseSize, phaseSize)


    # Make some random bubble data
    bubbles = []
    if drawBubbles:
        for i in range(100):
            bubbles.append(
                (random.randint(0, 512), # x
                random.randint(0, 512), # y
                random.randint(30, 100), # size
                random.random()) # phase
                )


    """ Start drawing """


    size(512, 512)

    def drawIcon(timeFactor):
        # timeFactor is the timeline position, between 0 and 1

        # Temporary background color
        #fill(0.85)
        #rect(0, 0, 512, 512)

        translate(256, 256)
        scale(1.1)
        translate(-256, -256)
        translate(-27, -51)


        fill(None)
        # Transparent shadow under the "D"
        with savedState():

            #fill(*darkOrange)
            stroke(*darkOrange)
            strokeWidth(60)

            drawPath(iconPath)


        # Gradient within the "D"
        save()
        # Clip
        clipPath(iconPath)
        # Move to the center of the canvas
        translate(256, 256)
        circleCount = 30
        for i in range(circleCount):
            f = i/circleCount
            angle = (f * 360) + (360 * timeFactor)
            x = 120 * sin(radians(angle+90))
            y = 120 * cos(radians(angle+90))
            colorFactor = f * f * f # Use an exponential curve for the color factor
            stroke(None)
            fill(*interpolateColor(colorFactor))
            #shadow((0, 0), 50, interpolateColor(colorFactor)) # Extra smoothness?
            oval(x-150, y-150, 300, 300)
        restore()

        # Bubbles
        for bubble in bubbles:
            save()
            clipPath(iconPath)
            translate(bubble[0], bubble[1])
            drawBubble(bubble[2], timeFactor + bubble[3])
            restore()

        # Pencil location
        angle = (f * 360) + (360 * timeFactor) + 70
        x = 120 * sin(radians(angle+90)) + 80
        y = 90 * cos(radians(angle+90)) + 10
        if not leftHand:
            x -= 60
            y -= 20

        # Shadow inside the "D"
        save()
        shadowPath = iconPath.copy()
        # Add the pencil shadow
        shadowX = 256
        shadowY = 300
        if leftHand:
            shadowX -= 40
            shadowY -= 10
        if drawPencil:
            if not bigPencil:
                shadowPath.oval(shadowX+x, shadowY+y, 50, 50)
        clipPath(iconPath)
        translate(-20, -20)
        strokeWidth(61)
        stroke(0, 0, 0, 0.25)
        drawPath(shadowPath)
        restore()

        # White stroke on top of the "D"
        fill(None)
        stroke(1)
        strokeWidth(30)
        drawPath(iconPath)

        # Pencil
        if drawPencil:
            save()
            translate(256, 286)
            # Rotate the pencil with each step
            pencilRotationAngle = 10 * cos(radians(angle))
            translate(x, y)
            # Pencil
            rotate(pencilRotationAngle)
            # And an additional amount for the base angle of the pencil
            if leftHand:
                rotate(50)
            else: rotate(-25)
            if bigPencil:
                scale(1.9, 1.9)
                strokeWidth(14)
                translate(25, 10)
            else: strokeWidth(18)
            fill(None)
            if reducedPalette:
                stroke(1)
                fill(*orange)
            else:
                stroke(*darkPurple)
                fill(*brightPurple)
            polygon((0, 0), (-40, 40), (-40, 140), (40, 140), (40, 40), close=True)
            # Pencil end
            oval(-40, 130, 80, 40)
            # Pencil tip
            if reducedPalette:
                fill(1)
            else: fill(*darkPurple)
            stroke(None)
            oval(-20, 0, 40, 40)
            restore()



    totalFrames = 21
    if tryAndError:
        totalFrames = 1
    for i in range(totalFrames):
        f = i / totalFrames
        if not i == 0:
            newPage()
        frameDuration(1/10)
        drawIcon(f)
        if not tryAndError:
            pass#saveImage(singleFileSavePath % i)


    if not tryAndError:
        saveImage(savePath)
