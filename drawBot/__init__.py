from .drawBotDrawingTools import _drawBotDrawingTool

_drawBotDrawingTool._addToNamespace(globals())


# This section is automatically generated with scripting/generateDrawbotInit.py
# and it should be updated each time the drawBot interface changes. It does not affect
# mere functionality, this is here to allow tools like mypy and pyright to perform
# static analysis on drawBot's code

# --- section automatically generated --- #
Variable = _drawBotDrawingTool.Variable
arc = _drawBotDrawingTool.arc
arcTo = _drawBotDrawingTool.arcTo
baselineShift = _drawBotDrawingTool.baselineShift
blendMode = _drawBotDrawingTool.blendMode
clipPath = _drawBotDrawingTool.clipPath
closePath = _drawBotDrawingTool.closePath
cmykFill = _drawBotDrawingTool.cmykFill
cmykLinearGradient = _drawBotDrawingTool.cmykLinearGradient
cmykRadialGradient = _drawBotDrawingTool.cmykRadialGradient
cmykShadow = _drawBotDrawingTool.cmykShadow
cmykStroke = _drawBotDrawingTool.cmykStroke
colorSpace = _drawBotDrawingTool.colorSpace
curveTo = _drawBotDrawingTool.curveTo
drawPath = _drawBotDrawingTool.drawPath
drawing = _drawBotDrawingTool.drawing
endDrawing = _drawBotDrawingTool.endDrawing
fallbackFont = _drawBotDrawingTool.fallbackFont
fill = _drawBotDrawingTool.fill
font = _drawBotDrawingTool.font
fontAscender = _drawBotDrawingTool.fontAscender
fontCapHeight = _drawBotDrawingTool.fontCapHeight
fontContainsCharacters = _drawBotDrawingTool.fontContainsCharacters
fontContainsGlyph = _drawBotDrawingTool.fontContainsGlyph
fontDescender = _drawBotDrawingTool.fontDescender
fontFileFontNumber = _drawBotDrawingTool.fontFileFontNumber
fontFilePath = _drawBotDrawingTool.fontFilePath
fontLeading = _drawBotDrawingTool.fontLeading
fontLineHeight = _drawBotDrawingTool.fontLineHeight
fontNamedInstance = _drawBotDrawingTool.fontNamedInstance
fontSize = _drawBotDrawingTool.fontSize
fontVariations = _drawBotDrawingTool.fontVariations
fontXHeight = _drawBotDrawingTool.fontXHeight
frameDuration = _drawBotDrawingTool.frameDuration
height = _drawBotDrawingTool.height
hyphenation = _drawBotDrawingTool.hyphenation
image = _drawBotDrawingTool.image
imagePixelColor = _drawBotDrawingTool.imagePixelColor
imageResolution = _drawBotDrawingTool.imageResolution
imageSize = _drawBotDrawingTool.imageSize
installFont = _drawBotDrawingTool.installFont
installedFonts = _drawBotDrawingTool.installedFonts
language = _drawBotDrawingTool.language
line = _drawBotDrawingTool.line
lineCap = _drawBotDrawingTool.lineCap
lineDash = _drawBotDrawingTool.lineDash
lineHeight = _drawBotDrawingTool.lineHeight
lineJoin = _drawBotDrawingTool.lineJoin
lineTo = _drawBotDrawingTool.lineTo
linearGradient = _drawBotDrawingTool.linearGradient
linkDestination = _drawBotDrawingTool.linkDestination
linkRect = _drawBotDrawingTool.linkRect
linkURL = _drawBotDrawingTool.linkURL
listColorSpaces = _drawBotDrawingTool.listColorSpaces
listFontGlyphNames = _drawBotDrawingTool.listFontGlyphNames
listFontVariations = _drawBotDrawingTool.listFontVariations
listLanguages = _drawBotDrawingTool.listLanguages
listNamedInstances = _drawBotDrawingTool.listNamedInstances
listOpenTypeFeatures = _drawBotDrawingTool.listOpenTypeFeatures
miterLimit = _drawBotDrawingTool.miterLimit
moveTo = _drawBotDrawingTool.moveTo
newDrawing = _drawBotDrawingTool.newDrawing
newPage = _drawBotDrawingTool.newPage
newPath = _drawBotDrawingTool.newPath
numberOfPages = _drawBotDrawingTool.numberOfPages
opacity = _drawBotDrawingTool.opacity
openTypeFeatures = _drawBotDrawingTool.openTypeFeatures
oval = _drawBotDrawingTool.oval
pageCount = _drawBotDrawingTool.pageCount
pages = _drawBotDrawingTool.pages
pdfImage = _drawBotDrawingTool.pdfImage
polygon = _drawBotDrawingTool.polygon
printImage = _drawBotDrawingTool.printImage
qCurveTo = _drawBotDrawingTool.qCurveTo
radialGradient = _drawBotDrawingTool.radialGradient
rect = _drawBotDrawingTool.rect
restore = _drawBotDrawingTool.restore
rotate = _drawBotDrawingTool.rotate
save = _drawBotDrawingTool.save
saveImage = _drawBotDrawingTool.saveImage
savedState = _drawBotDrawingTool.savedState
scale = _drawBotDrawingTool.scale
shadow = _drawBotDrawingTool.shadow
size = _drawBotDrawingTool.size
sizes = _drawBotDrawingTool.sizes
skew = _drawBotDrawingTool.skew
strikethrough = _drawBotDrawingTool.strikethrough
stroke = _drawBotDrawingTool.stroke
strokeWidth = _drawBotDrawingTool.strokeWidth
tabs = _drawBotDrawingTool.tabs
text = _drawBotDrawingTool.text
textBox = _drawBotDrawingTool.textBox
textBoxBaselines = _drawBotDrawingTool.textBoxBaselines
textBoxCharacterBounds = _drawBotDrawingTool.textBoxCharacterBounds
textOverflow = _drawBotDrawingTool.textOverflow
textProperties = _drawBotDrawingTool.textProperties
textSize = _drawBotDrawingTool.textSize
tracking = _drawBotDrawingTool.tracking
transform = _drawBotDrawingTool.transform
translate = _drawBotDrawingTool.translate
underline = _drawBotDrawingTool.underline
uninstallFont = _drawBotDrawingTool.uninstallFont
url = _drawBotDrawingTool.url
width = _drawBotDrawingTool.width
writingDirection = _drawBotDrawingTool.writingDirection

# directly import FormattedString, BezierPath, and ImageObject as classes
from drawBot.context.baseContext import FormattedString, BezierPath
from drawBot.context.tools.imageObject import ImageObject

from drawBot.context.tools import drawBotbuiltins
lerp = drawBotbuiltins.lerp
norm = drawBotbuiltins.norm
remap = drawBotbuiltins.remap