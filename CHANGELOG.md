# Changelog For DrawBot


## [3.124] 


## [3.123]

- Built with Github actions!!!!
- Improve pip installer.
- Support `viewBox` in svg output.
- Point attributes of a bezierPath are immutable.

## [3.122]

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
