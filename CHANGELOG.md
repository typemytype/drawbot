# Changelog For DrawBot

## [3.127] 2021-??

- Allow `Path` objects in places where a path is an argument: `saveImage(pathObject)`, `image(pathObject, ...)` 
- Add support for asyncio by lauching the app with corefoundationasyncio.
- Remove `mov` context in favor of `mp4` as `QTKit` is not supported anymore.

## [3.126] 2020-07-02

- Improve update checker.
- Fix docs for `listOpenTypeFeatures`.
- Add argument while saving an animated gif: `loop`.
- Add argument while saving an image: `antiAliasing`.
- Improve the difference between kerning (an OpenType feature) and tracking (adding white space between characters).
- Add `textBoxCharacterBounds(text, box)` returning a list of typesetted bounding boxes.
- Improve `text(..)` typesetting with multiline text and paragraph styles.
- Add `formattedString.url(url)`.
- Add `linkURL(url, box)`. 
- Add option `continuous` in `Variable(.., continuous=False)`.

## [3.125] 2020-04-22

- Update embedded uharfbuzz.
- Embed setuptool and packaging.
- Fix drawbot://url/to/python.py.
- Improve tracking documenation.

## [3.124] 2020-03-28

- Fix updater with the correct download link.
- Allowing external tools to be used inside DrawBot, a notarizing entitlement.

## [3.123] 2020-03-03

- Fully notarized and built with GitHub Actions!!!!
- Improve pip installer.
- Support `viewBox` in svg output.
- Point attributes of a BezierPath are immutable.
- Fix bug when an FormattedString contains an empty last line.
- Don't optimize an empty BezierPath.
- Improve updater message.
- Upgrade code editor lexer to python3.
- Upgrade internal tool potrace and mkbitmap.
- Add context-specific attributes for BezierPath and FormattedString: `svgLink`, `svgID`, `svgClass`.

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
