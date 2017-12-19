# DrawBot

DrawBot is a powerful, free application for MacOSX that invites you to write simple Python scripts to generate two-dimensional graphics. The built-in graphics primitives support rectangles, ovals, (bezier) paths, polygons, text objects and transparency.

To download the latest version of the app, go to  
http://www.drawbot.com/content/download.html

---

## Using DrawBot as a Python module

DrawBot can also be installed as a Python module, the app is not required. 

#### Install 

download: https://github.com/typemytype/drawbot/archive/master.zip

run `cd <path/where/you/have/downloaded/and/unzipped/drawBot>`
run `python setupAsModule.py install`

#### Usage

```Python
    import drawBot

    drawBot.newDrawing()
    drawBot.newPage(1000, 1000)
    drawBot.rect(10, 10, 100, 100)
    drawBot.saveImage("~/Desktop/aRect.png")
    drawBot.endDrawing()
```

It is adviced to start with `newDrawing()` and end with `endDrawing()`, to clear the instruction stack and remove installed fonts.

---

## Compile DrawBot from source

#### compile drawBot.app (with UI)

__Required packages:__

(Most of these are available through `pip`.)

* [vanilla](https://github.com/typesupply/vanilla)
* [defcon](https://github.com/typesupply/defcon)
* [defconAppKit](https://github.com/typesupply/defconAppKit)
* ~~[robofab](https://github.com/robofab-developers/robofab)~~ (not used anymore)
* [fontTools](https://github.com/behdad/fonttools)
* [pygments](http://pygments.org)
* [jedi](http://jedi.jedidjah.ch/en/latest/)
* [booleanOperations](https://github.com/typemytype/booleanOperations)
* [mutatorMath](https://github.com/LettError/MutatorMath)
* [woffTools](https://github.com/typesupply/woffTools)
* [compositor](https://github.com/typesupply/compositor)
* [feaTools2](https://github.com/typesupply/feaTools2)
* [ufo2svg](https://github.com/typesupply/ufo2svg)
* [fontTools](https://github.com/fonttools/fonttools)
* [PyObjC](https://pythonhosted.org/pyobjc/) (Only if you're not building with the system Python 2.7)

__Compile:__


DrawBot is compiled with [py2app](https://pypi.python.org/pypi/py2app/) into an application package.


    cd path/To/drawBot
    python setup.py py2app


#### compile drawBot Python module only


This module only works on Mac OS as it requires `PyObjC`, `AppKit`, `CoreText` `Quartz` and more.

__Required packages:__

* [vanilla](https://github.com/typesupply/vanilla)
* [defconAppKit](https://github.com/typesupply/defconAppKit)
* [fontTools](https://github.com/behdad/fonttools)

__Compile:__

	cd path/To/drawBot
    python setupAsModule.py install
