#!/usr/bin/env python
from distutils.core import setup

from drawBotSettings import __version__

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
    package_dir={"": ""}
    )