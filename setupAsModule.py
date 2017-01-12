#!/usr/bin/env python
from setuptools import setup

from drawBot.drawBotSettings import __version__

try:
    import fontTools
except:
    print "*** Warning: drawBot requires FontTools, see:"
    print "    https://github.com/behdad/fonttools"


try:
    import vanilla
except:
    print "*** Warning: drawBot requires vanilla, see:"
    print "    https://github.com/typesupply/vanilla"


try:
    import defconAppKit
except:
    print "*** Warning: drawBot requires defconAppKit, see:"
    print "    https://github.com/typesupply/defconAppKit"


setup(name="drawBot",
    version=__version__,
    description="DrawBot is a powerful tool that invites you to write simple Python scripts to generate two-dimensional graphics. The builtin graphics primitives support rectangles, ovals, (bezier) paths, polygons, text objects and transparency.",
    author="Just van Rossum, Erik van Blokland, Frederik Berlaen",
    author_email="frederik@typemytype.com",
    url="http://drawbot.com",
    license="BSD",
    packages=[
        "drawBot",
        "drawBot.context",
        "drawBot.context.tools",
        "drawBot.ui"
        ],
    package_data = {
        "drawBot" : [
            "context/tools/gifsicle",
            "context/tools/mkbitmap",
            "context/tools/potrace"
            ]
        },
    include_package_data=True,
    )
