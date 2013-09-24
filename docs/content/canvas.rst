Canvas
======

The canvas is the thing DrawBot draws on. It's the document size, the art board. It has a height and a width which can be set. The dimensions of the canvas are not related to the size of the window.

**The origin of the drawing board is at the bottom left.**

Size
----

.. autofunction:: drawBot.size

Pages
-----

.. autofunction:: drawBot.newPage

State
-----

.. autofunction:: drawBot.save
.. autofunction:: drawBot.restore

Transformations
---------------

.. autofunction:: drawBot.translate
.. autofunction:: drawBot.rotate
.. autofunction:: drawBot.scale
.. autofunction:: drawBot.skew
.. autofunction:: drawBot.transform((xx, xy, yx, yy, x, y))

Saving
------

.. autofunction:: drawBot.saveImage