Code Editor
===========

The place where you can tell Python to draw things on the page and/or print things in the console.

The syntax colors can be customized in the :doc:`preferences` window.

Code interaction
----------------

The code editor also makes it easy and fun to interact with values in your program. When selected, some kinds of Python objects can be modified dynamically by pressing the Cmd key. The effects depend on the type of object:

- `bool`: select and Cmd-click to turn the value on/off like a switch.
- `int` or `float`: select the number, press Cmd and move the mouse up/down or right/left to increase/decrease the number. The default step is 1, by pressing alt the step is changed to 0.1. Additional shift can be pressed to multiply the steps by 10. Using the arrow keys also works.
- in `tuples` with numbers it is possible to select two neighbouring numbers and modify them together at the same time – this is specially useful when working with coordinate pairs or dimensions.

.. raw:: html ::

	<iframe src="http://player.vimeo.com/video/89407186" width="500" height="328" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>

Live coding
-----------

The live coding mode executes the code as you type, so you can see changes without having to re-run the program every time. This is useful when working with text or making demonstrations.

This feature can be turned on/off in the Python menu.

Use it with caution: depending on the size of your program and the amount of interaction, Drawbot can get a bit slow.