Compile DrawBot
===============

drawBot.app
-----------

### Required packages:

* [vanilla](https://github.com/typesupply/vanilla)
* [defcon](https://github.com/typesupply/defcon)
* [defconAppKit](https://github.com/typesupply/defconAppKit)
* [robofab](https://github.com/robofab-developers/robofab)
* [fontTools](https://github.com/behdad/fonttools)
* [pygments](http://pygments.org)
* [jedi](http://jedi.jedidjah.ch/en/latest/)
* [booleanOperations](https://github.com/typemytype/booleanOperations)
* [mutatorMath](https://github.com/LettError/MutatorMath)
* [woffTools](https://github.com/typesupply/woffTools)
* [compositor](https://github.com/typesupply/compositor)
* [feaTools2](https://github.com/typesupply/feaTools2)
* [ufo2svg](https://github.com/typesupply/ufo2svg)
* [fontTools](https://github.com/behdad/fontTools)

### Compile:


DrawBot is compiled with [py2app](https://pypi.python.org/pypi/py2app/) into an application package.


    cd path/To/drawBot
    python setup.py py2app


drawBot as module
-----------------

### Required packages:

This module only works on OSx as it requires `AppKit`, `CoreText` and `Quartz`.

* [vanilla](https://github.com/typesupply/vanilla)
* [defconAppKit](https://github.com/typesupply/defconAppKit)
* [fontTools](https://github.com/behdad/fonttools)

### Compile:

	cd path/To/drawBot
    python setupAsModule.py install
