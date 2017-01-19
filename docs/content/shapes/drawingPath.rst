Drawing Paths
=============

Using bezier paths.

.. autofunction:: drawBot.newPath
.. autofunction:: drawBot.moveTo
.. autofunction:: drawBot.lineTo
.. autofunction:: drawBot.curveTo
.. autofunction:: drawBot.arc
.. autofunction:: drawBot.arcTo
.. autofunction:: drawBot.closePath
.. autofunction:: drawBot.drawPath

.. downloadcode:: path.py

    # create a new empty path
    newPath()
    # set the first oncurve point
    moveTo((100, 100))
    # line to from the previous point to a new point
    lineTo((100, 200))
    lineTo((200, 200))

    # curve to a point with two given handles
    curveTo((200, 100), (150, 100), (100, 100))

    # close the path
    closePath()
    # draw the path
    drawPath()

.. autofunction:: drawBot.clipPath

.. downloadcode:: clipPath.py

    # create a bezier path
    path = BezierPath()

    # move to a point
    path.moveTo((100, 100))
    # line to a point
    path.lineTo((100, 200))
    path.lineTo((200, 200))
    # close the path
    path.closePath()
    # set the path as a clipping path
    clipPath(path)
    # the oval will be clipped inside the path
    oval(100, 100, 100, 100)
