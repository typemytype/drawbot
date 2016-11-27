DrawBot as a module
===================

DrawBot can also be installed as a module, the app is not required. 


Install 
-------

run `python setupAsModule.py install`

Usage
-----

```Python
import drawBot

drawBot.newDrawing()
drawBot.newPage(1000, 1000)
drawBot.rect(10, 10, 100, 100)
drawBot.saveImage("~/Desktop/aRect.png")
drawBot.endDrawing()
```

It is adviced to start with `newDrawing()` and end with `endDrawing()`, to clear the instruction stack and remove installed fonts.

