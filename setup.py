#!/usr/bin/env python
from __future__ import division, absolute_import, print_function
from setuptools import setup
import os
import re
import shutil


_versionRE = re.compile(r'__version__\s*=\s*\"([^\"]+)\"')
# read the version number for the settings file
with open('drawBot/drawBotSettings.py', "r") as settings:
    code = settings.read()
    found = _versionRE.search(code)
    assert found is not None, "drawBot __version__ not found"
    __version__ = found.group(1)


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
    install_requires=[
        "pyobjc",
        "fontTools",
        "booleanOperations",
        "pillow"
    ],
    include_package_data=True,
)

# remove all external tools
for externalTool in externalTools:
    dest = os.path.join(externalToolsDestRoot, externalTool)
    os.remove(dest)
