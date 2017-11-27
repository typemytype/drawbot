#!/usr/bin/env python
from setuptools import setup
import os
import shutil

from drawBot.drawBotSettings import __version__

try:
    import fontTools
except ImportError:
    print "*** Warning: drawBot requires FontTools, see:"
    print "    https://github.com/behdad/fonttools"


try:
    import vanilla
except ImportError:
    print "*** Warning: drawBot requires vanilla, see:"
    print "    https://github.com/typesupply/vanilla"


try:
    import defconAppKit
except ImportError:
    print "*** Warning: drawBot requires defconAppKit, see:"
    print "    https://github.com/typesupply/defconAppKit"


externalTools = ("ffmpeg", "gifsicle", "mkbitmap", "potrace")
externalToolsSourceRoot = os.path.join(os.path.dirname(__file__), "Resources", "externalTools")
externalToolsDestRoot = os.path.join(os.path.dirname(__file__), "drawBot", "context", "tools")

# copy all external tools into drawBot.context.tools  folder
for externalTool in externalTools:
    source = os.path.join(externalToolsSourceRoot, externalTool)
    dest = os.path.join(externalToolsDestRoot, externalTool)
    shutil.copyfile(source, dest)
    os.chmod(dest, 0o775)


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
    package_data={
        "drawBot": [
            "context/tools/ffmpeg",
            "context/tools/gifsicle",
            "context/tools/mkbitmap",
            "context/tools/potrace"
        ]
    },
    include_package_data=True,
)

# remove all external tools
for externalTool in externalTools:
    dest = os.path.join(externalToolsDestRoot, externalTool)
    os.remove(dest)
