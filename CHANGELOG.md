# Changelog For DrawBot


## [3.124] Unreleased


## [3.123] 2020-03-02

- Built with Github actions!!!!
- Improve pip installer.
- Support `viewBox` in svg output.
- Point attributes of a bezierPath are immutable.
- Fix bug when an formattedString contains an empty last line.
- Don't optimize an empty bezierPath.
- Improve updater message.
- Upgrade code editor lexer to python3.
- Upgrade internal tool potrace and mkbitmap.

## [3.122] 2019-11-03

- Adding bezierPath.expandStroke(width, lineCap="round", lineJoin="round", miterLimit=10) (thanks to Bahman Eslami)
- Improved internal OpenType feature tags setting
- Improved complex formattedString type setting
- Improved alignment with text() and FormattedString
- Added a DrawBot frontend for pip/PyPI to make it super easy to install third-party packages: see menu Python -> Install Python Packages
- Fixed text stroke behavior (but is a breaking change): strokeWidth on text no longer scales with the fontSize
- Removed support for .mov export on 10.15 and up (QTKit is no longer supported there)
- Fixed extracting single frames from .gif files
- Improved setup.py, so drawbot-as-a-module can be easily installed with pip using a github URL
- All test now run on Travis CI (and soon also on GitHub Actions)
- Removed Python 2 code
- Many small issues were fixed

## [3.121] 2019-10-04


## [3.120] 2019-03-13