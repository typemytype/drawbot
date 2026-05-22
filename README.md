![DrawBot Test Bench](https://github.com/typemytype/drawbot/workflows/DrawBot%20Test%20Bench/badge.svg)
![DrawBot App Builder](https://github.com/typemytype/drawbot/workflows/DrawBot%20App%20Builder/badge.svg)
[![codecov](https://codecov.io/gh/typemytype/drawbot/branch/master/graph/badge.svg)](https://codecov.io/gh/typemytype/drawbot)

# DrawBot

DrawBot is a powerful, free application for macOS that invites you to write Python scripts to generate two-dimensional graphics. The built-in graphics primitives support rectangles, ovals, (bezier) paths, polygons, text objects, colors, transparency and much more. You can program multi-page documents and stop-motion animations. Export formats include PDF, SVG, PNG, JPEG, TIFF, animated GIF and MP4 video.

To download the latest version of the app, go to
http://www.drawbot.com/content/download.html

---

## Using DrawBot as a Python module

DrawBot can also be installed as a Python module, the app is not required. It works on Python3.11+.

#### Install

The easiest way is to use pip:

	pip install git+https://github.com/typemytype/drawbot

To install it manually, follow these instructions:

download: https://github.com/typemytype/drawbot/archive/master.zip

run `cd <path/where/you/have/downloaded/and/unzipped/drawBot>`
run `python setup.py install`

#### Usage

```Python
import drawBot

with drawBot.drawing():
    drawBot.newPage(1000, 1000)
    drawBot.rect(10, 10, 100, 100)
    drawBot.saveImage("~/Desktop/aRect.png")
```

It is adviced to wrap your drawing instructions into a `with drawbot.drawing()` statement, to clear the instruction stack and remove installed fonts.

---

## Compile DrawBot from source

#### compile drawBot.app (with UI)

__Required packages:__

(Most of these are available through `pip`.)

* [vanilla](https://github.com/typesupply/vanilla)
* [defcon](https://github.com/typesupply/defcon)
* [defconAppKit](https://github.com/typesupply/defconAppKit)
* [fonttools](https://github.com/fonttools/fonttools)
* [pygments](http://pygments.org)
* [jedi](http://jedi.jedidjah.ch/en/latest/)
* [booleanOperations](https://github.com/typemytype/booleanOperations)
* [mutatorMath](https://github.com/LettError/MutatorMath)
* [woffTools](https://github.com/typesupply/woffTools)
* [compositor](https://github.com/typesupply/compositor)
* [feaTools2](https://github.com/typesupply/feaTools2)
* [ufo2svg](https://github.com/typesupply/ufo2svg)
* [PyObjC](https://github.com/ronaldoussoren/pyobjc)
* [PIL](https://github.com/python-pillow/Pillow) (only for running tests)

__Compile:__


DrawBot is compiled with [py2app](https://pypi.python.org/pypi/py2app/) into an application package.


    cd path/To/drawBot
    python setupApp.py py2app


#### compile drawBot Python module only


This module only works on Mac OS as it requires `PyObjC`, `AppKit`, `CoreText` `Quartz` and more.

__Required packages:__

* [vanilla](https://github.com/typesupply/vanilla)
* [defconAppKit](https://github.com/typesupply/defconAppKit)
* [fontTools](https://github.com/behdad/fonttools)

__Compile:__

	cd path/To/drawBot
    python setup.py install


## [Release protocol](https://github.com/typemytype/drawbot/wiki/DrawBot-release-protocol)

---

## Development

### Setup

From the repository root, create a virtual environment, activate it, and install both the package and test dependencies:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt -r test-requirements.txt

### Running the tests

From the repository root (with the environment activated):

    python tests/runAllTests.py

`runAllTests.py` discovers every `test*.py` module under `tests/`. Individual test modules can also be executed directly (e.g. `python tests/testExport.py`).

The runtime dependencies for the test suite (`Pillow`, `attrs`, `packaging`, `mypy`, `ruff`, `ruff-api`) live in `test-requirements.txt`.

### Benchmarks and tempTestData

`tests/data/` is the benchmark folder. Filenames follow a prefix convention:

- `expected_<name>.<ext>` — reference output for `testScripts.py` and parts of `testExport.py`.
- `example_<name>.png` — reference renders for `testExamples.py` (also used by the docs site).
- no prefix — assets consumed by the test scripts themselves (sample images, fonts, etc.).

Freshly rendered output goes into `tests/tempTestData/` (gitignored). When a comparison fails, that's where you'll find the actual rendered file alongside the expected one.

### Rendering drift across macOS versions and CI

Quartz / Core Image rendering is not bit-identical across macOS versions, so the comparison helpers in `testSupport.py` fall back to a fuzzy image diff with a small tolerance whenever raw byte equality fails. Even so, CI on GitHub Actions might run on a different macOS image than your machine, and some tests may pass locally while failing in CI (or vice versa). To find the exact macOS version GitHub Actions is using, open the workflow webpage, expand the **Set up job** step, and read the `Image OS` / `Runner Image` lines in its log.

To investigate further, use `tests/differenceBuilder.py`. It builds a PDF report visualizing the diff between a folder of freshly rendered images and the benchmarks in `tests/data/`. For each pair it lays out the new render, the expected image tracked in the benchmark folder, a pixel-difference image, and a histogram side by side. Pages where the fuzzy similarity exceeds the tolerance are drawn with a red border so failures are easier to spot. Run it as:

    python tests/differenceBuilder.py <folder_with_renders> <output.pdf>

or invoke it with no arguments to pick the folders via a dialog. The resulting PDF is generated on the fly and not committed.

When a test passes locally but fails in CI (or vice versa):

1. Pull the failing artifacts from the Github Actions failed workflow and check the "Drawbot Test Differences" PDF. Keep the "DrawBot Temp Data Results" at hand as well.
2. If the difference between the images is small and clearly attributable to an OS version change (check the overlay and the histogram), the benchmark in `tests/data/` can be updated — but don't blindly copy the CI render over the local one, remember to add the correct prefix as needed.
3. If the difference is large, treat it as a real problem.
