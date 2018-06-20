DrawBot Icon
============

The making of (by Andy Clymer)

.. downloadcode:: drawBotIcon.py

    from ufoLib.glifLib import readGlyphFromString
    from fontParts.fontshell.glyph import RGlyph
    import random
    import os

    # settings
    totalFrames = 1

    drawPencil = True
    drawBubbles = True

    # color settings
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
    iconGlifString = """<?xml version="1.0" encoding="UTF-8"?>
    <glyph name="D" format="2">
      <advance width="500"/>
      <outline>
        <contour>
          <point x="61" y="455" type="line"/>
          <point x="348" y="501"/>
          <point x="464" y="434"/>
          <point x="464" y="259" type="curve" smooth="yes"/>
          <point x="464" y="82"/>
          <point x="348" y="15"/>
          <point x="61" y="61" type="curve"/>
        </contour>
        <contour>
          <point x="212" y="321" type="curve"/>
          <point x="212" y="195" type="line"/>
          <point x="283" y="190"/>
          <point x="314" y="210"/>
          <point x="314" y="259" type="curve" smooth="yes"/>
          <point x="314" y="307"/>
          <point x="283" y="327"/>
        </contour>
      </outline>
    </glyph>
    """


    ########

    if __file__:
        # store generated assets next to this file
        folderPath = os.path.split(__file__)[0]
    else:
        # file is unsaved, store the generated assets on the desktop
        folderPath = "~/Desktop"
        
    savePath = os.path.join(folderPath, "icon.gif")

    # Read the string into a glyph object
    iconGlyph = RGlyph()
    pen = iconGlyph.getPointPen()
    readGlyphFromString(iconGlifString, glyphObject=iconGlyph, pointPen=pen)

    # Fetch the path of the glyph as a NSBezierPath
    iconPath = BezierPath()
    iconGlyph.draw(iconPath)
    # Remove the inside contour of the glyph, and read another path
    iconGlyph.removeContour(1)
    # Fetch the path of the glyph as a NSBezierPath
    iconOutsidePath = BezierPath()
    iconGlyph.draw(iconOutsidePath)


    # Helper functions

    def interpolate(f, a, b):
        """
        Interpolate between two numbers with given factor.
        """
        v = (a + (b - a) * f)
        return v

    def interpolateColor(f, color0=None, color1=None):
        """
        Interplate between color list with a given factor.
        """
        if not color0:
            color0 = lightOrange
        if not color1:
            color1 = orange
        newColor = []
        # interpolate
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

    # Start drawing

    def drawIcon(timeFactor):
        # timeFactor is the timeline position, between 0 and 1
        # Temporary background color
        fill(1)
        rect(0, 0, 512, 512)
        
        fill(None)
        # Transparent shadow under the "D"
        with savedState():
            #fill(*darkOrange)
            stroke(*darkOrange)
            strokeWidth(60)        
            drawPath(iconPath)
        
        
        # Gradient within the "D"
        with savedState():    
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
        
        # Bubbles
        for bubble in bubbles:
            with savedState():    
                clipPath(iconPath)
                translate(bubble[0], bubble[1])
                drawBubble(bubble[2], timeFactor + bubble[3])
        
        # Pencil location
        angle = (f * 360) + (360 * timeFactor) + 70
        x = 120 * sin(radians(angle+90)) + 20
        y = 90 * cos(radians(angle+90)) - 10
        
        # Shadow inside the "D"
        with savedState():
            shadowPath = iconPath.copy()
            # Add the pencil shadow
            if drawPencil:        
                shadowPath.oval(256+x, 300+y, 50, 50)
            clipPath(iconPath)
            translate(-20, -20)
            strokeWidth(61)
            stroke(0, 0, 0, 0.25)
            drawPath(shadowPath)
        
        # White stroke on top of the "D"
        fill(None)
        stroke(1)
        strokeWidth(30)
        drawPath(iconPath)
        
        # Pencil
        if drawPencil:
            with savedState():
                translate(230, 230)
                # Rotate the pencil with each step
                pencilRotationAngle = 10 * cos(radians(angle))
                translate(x, y)
                # Pencil
                rotate(pencilRotationAngle)
                rotate(-25) # And an additional amount for the base angle of the pencil
                strokeWidth(18)
                fill(None)
                stroke(*darkPurple)
                fill(*brightPurple)
                polygon((0, 0), (-40, 40), (-40, 140), (40, 140), (40, 40), close=True)
                # Pencil end
                oval(-40, 130, 80, 40)
                # Pencil tip
                fill(*darkPurple)
                stroke(None)
                oval(-20, 0, 40, 40)
            

    # start the program
    for i in range(totalFrames):
        # calculate the factor
        f = i / totalFrames
        # create a new page
        newPage(512, 512)
        # set frame duration
        frameDuration(1/10)
        # draw an versionof the icon with a given factor
        drawIcon(f)
                
    # save the image as movie
    saveImage(savePath)
