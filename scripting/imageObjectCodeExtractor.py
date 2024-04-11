from pathlib import Path

import AppKit
import Quartz

"""
Notes 10/01:
- remove double comments (inside and outside the docstring)
- check hints + syntax
- add very simple test to suite, just run each filter
- remove “ ” typographical quotes from docstrings

"""

class CodeWriter:

    def __init__(self, INDENT="    "):
        self.code = [
            "# the following code is automatically generated with `scripting/imageObjectCodeExtractor.py`",
            "# please, do not attempt to edit it manually as it will be overriden in the future",
            ""
        ]
        self.INDENT = INDENT
        self.indentLevel = 0

    def indent(self):
        self.indentLevel += 1

    def dedent(self):
        self.indentLevel -= 1

    def add(self, line):
        self.code.append(f"{self.INDENT * self.indentLevel}{line}")

    def addDict(self, attribute, data, space=" ", trailing=""):
        self.add(f"{attribute}{space}={space}dict(")
        self.indent()

        for index, (key, value) in enumerate(data.items()):
            if isinstance(value, dict):
                if value:
                    trailing = "" if index == len(data) - 1 else ","
                    self.addDict(key, value, space="", trailing=trailing)
            else:
                comma = ","
                if index == len(data) - 1:
                    comma = ""
                self.add(f"{key}={value}{comma}")
        self.dedent()
        self.add(f"){trailing}")

    def appendCode(self, otherCode):
        for line in otherCode.code:
            self.add(line)

    def __repr__(self):
        return self.INDENT  + f"\n{self.INDENT}".join(self.code)




def camelCase(txt):
    if len(txt) > 2 and txt[1].isupper():
        return txt
    if txt.isupper():
        return txt
    return txt[0].lower() + txt[1:]


converters = {

    "center" : "AppKit.CIVector.vectorWithX_Y_({inputKey}[0], {inputKey}[1])",
    "mask" : "{inputKey}._ciImage()",

    "neutral" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 2)",
    "targetNeutral" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 2)",
    "point0" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 2)",
    "topLeft" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 2)",
    "topRight" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 2)",
    "bottomLeft" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 2)",
    "bottomRight" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 2)",
    "color" : "AppKit.CIColor.colorWithRed_green_blue_alpha_({inputKey}[0], {inputKey}[1], {inputKey}[2], {inputKey}[3])",
    "extent" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 4)",
    "rectangle" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 4)",
    "lightPosition" : "AppKit.CIVector.vectorWithValues_count_({inputKey}, 3)",
    "angle" : "radians({inputKey})",
    "message" : "AppKit.NSData.dataWithBytes_length_({inputKey}, len({inputKey}))",
    "text": "text.getNSObject()"
}

variableValues = {
    "image" : "an Image object",
    "size" : "a tuple (w, h)",
    "center" : "a tuple (x, y)",
    "angle": "a float in degrees",
    "minComponents" : "RGBA tuple values for the lower end of the range.",
    "maxComponents" : "RGBA tuple values for the upper end of the range.",
    "RVector" : "RGBA tuple values for red.",
    "GVector" : "RGBA tuple values for green.",
    "BVector" : "RGBA tuple values for blue.",
    "AVector" : "RGBA tuple values for alpha.",
    "BiasVector" : "RGBA tuple values for bias.",
    "neutral" : "a tuple",
    "targetNeutral" : "a tuple",
    "point0" : "a tuple (x, y)",
    "color" : "RGBA tuple Color (r, g, b, a)",
    "alwaysSpecifyCompaction" : "a bool",
    "rectangle" : "a tuple (x, y, w, h)",
    "compactStyle" : "a bool",
    "message" : "a string",
    "text": "a `FormattedString`",
    "shadowOffset" : "a tuple (x, y)",
    "lightPosition" : "a tulple (x, y, z)",
    "correctionLevel" : "a string, options are 'L', 'M', 'Q', 'H'",
    "transform" : "a tuple (xx, xy, yx, yy, x, y)",
    "colorSpace": "a CoreGraphics color space"
}

numbers = [
    'saturation', 'shadowAmount', 'power', 'acuteAngle', 'sharpness', 'radius', 'GCR', 'EV',
    'UCR', 'bias', 'brightness', 'noiseLevel', 'barOffset', 'intensity', 'shadowSize', 'amount',
    'levels', 'aspectRatio', 'contrast',
    "bottomHeight", "centerStretchAmount",
    "closeness1", "closeness2", "closeness3", "layers", "compactionMode", "compression",
    "opacity", "shadowRadius", "weights", "width", "zoom", "correctionLevel", "lowLimit",
    "maxHeight", "edgeIntensity", "epsilon",
    "maxStriationRadius", "rotation", "radius0", "radius1", "quietSpace",
    "maxWidth", "dataColumns", "decay",
    "minHeight", "crossAngle", "crossOpacity", "crossScale", "crossWidth",
    "minWidth", "contrast1", "contrast2", "contrast3", "count", "cropAmount",
    "numberOfFolds", "concentration", "fadeThreshold", "foldShadowAmount",
    "haloOverlap", "haloRadius", "haloWidth", "height", "highLimit", "highlightAmount",
    "rows", "strands", "striationContrast", "striationStrength", "sunRadius",
    "scale", "periodicity", "preferredAspectRatio", "refraction", "shadowDensity", "threshold", "time",
    "unsharpMaskIntensity", "unsharpMaskRadius"

]

for n in numbers:
    variableValues[n] = "a float"


argumentToHint = {
    "text": ": FormattedString",
    "message": ": str"
}

toCopy = {

    "image" : ("mask", "disparityImage", "texture", "displacementImage", "gradientImage", "backgroundImage", "backsideImage", "maskImage", "shadingImage", "targetImage", "gainMap", "glassesImage", "hairImage", "matteImage"),
    "message": ("cube0Data", "cube1Data"),
    "rectangle" : ("extent", "minComponents", "maxComponents", "shadowExtent", "RVector", "GVector", "BVector", "AVector", "BiasVector", "redCoefficients", "greenCoefficients", "blueCoefficients", "alphaCoefficients", "biasVector"),
    "color" : ("replacementColor3", "color0", "centerColor1", "centerColor3", "replacementColor1", "centerColor2", "replacementColor2", "color1", "color2"),

    "point0" : ("lightPointsAt", "shadowOffset", "point", "point1", "point2", "point3", "point4", "insetPoint0", "insetPoint1", "topLeft", "topRight", "bottomLeft", "bottomRight"),

    "lightPosition" : ("lightPointsAt"),

    "angle" : ("acuteAngle", "crossAngle"),
}

for k, v in toCopy.items():
    for n in v:
        if k in converters:
            converters[n] = converters[k]
        if k in variableValues:
            variableValues[n] = variableValues[k]


ignoreInputKeys = ["inputImage"]

generators = list(AppKit.CIFilter.filterNamesInCategory_("CICategoryGenerator")) # type: ignore
generators.extend([
    "CIPDF417BarcodeGenerator",
    "CIGaussianGradient",
    "CILinearGradient",
    "CIRadialGradient",
    "CISmoothLinearGradient",

])


allFilterNames =  AppKit.CIFilter.filterNamesInCategory_(None) # type: ignore

excludeFilterNames = [
    "CIBarcodeGenerator",
    "CIBicubicScaleTransform",
    "CIMedianFilter",
    "CIColorCube",
    "CIColorCubeWithColorSpace",
    # this one requires a colorspace which is difficult to express for regular drawBot users
    # little use for a filter like this, it does not make sense to abstract this for now
    # no default value for the colorspace makes it difficult to use it
    "CIColorCubesMixedWithMask",
    "CIAffineTransform",
]

degreesAngleFilterNames = [
    "CIVortexDistortion"

]

def pythonifyDescription(description):
    search = [
        ("@YES", "`True`"),
        ("@NO", "`False`"),
        ("radians", "degrees"),
        ("nil", "`None`"),
        ("CGColorSpaceRef", "color space"),
        ("CGColorSpace", "color space"),

    ]
    for s, r in search:
        description = description.replace(s, r)
    return description


if __name__ == '__main__':
    code = CodeWriter()

    for filterName in allFilterNames:
        if filterName in excludeFilterNames:
            continue
        ciFilter = AppKit.CIFilter.filterWithName_(filterName) # type: ignore
        ciFilterAttributes = ciFilter.attributes()
        doc = CodeWriter()
        doc.add(AppKit.CIFilter.localizedDescriptionForFilterName_(filterName)) # type: ignore

        args = []
        inputCode = CodeWriter()

        inputKeys = [inputKey for inputKey in ciFilter.inputKeys() if inputKey not in ignoreInputKeys]
        # this sorts the arguments by setting the ones without default first to avoid a syntax error
        # in the python code generated automatically
        inputKeys.sort(key=lambda x: bool(ciFilterAttributes.get(x, dict()).get("CIAttributeDefault") is not None))

        attributes = dict()

        if inputKeys:
            doc.add("")
            doc.add("Attributes:")
            doc.indent()
            if filterName in generators:
                args.append("size: Size")
                doc.add(f"`size` {variableValues['size']}")
            for inputKey in inputKeys:
                info = ciFilterAttributes.get(inputKey)

                default = info.get("CIAttributeDefault")
                description = info.get("CIAttributeDescription", "")
                inputKey = camelCase(inputKey[5:])
                arg = inputKey

                # if "Set to nil for automatic." in description:
                #     default = "None"

                if inputKey in toCopy["image"]:
                    arg += ": Self"

                if inputKey in argumentToHint:
                    arg += argumentToHint[inputKey]

                # if filterName == "CIPDF417BarcodeGenerator":
                #     print(inputKeys)
                #     print(ciFilterAttributes)
                #     raise Exception

                if default is not None:
                    if isinstance(default, AppKit.CIVector): # type: ignore
                        if default.count() == 2:
                            default = default.X(), default.Y()
                            arg += ": Point"
                        elif default.count() == 4:
                            default = default.X(), default.Y(), default.Z(), default.W()
                            arg += ": BoundingBox"
                        else:
                            default = tuple(default.valueAtIndex_(i) for i in range(default.count()))
                            arg += ": tuple"

                    elif isinstance(default, AppKit.NSAffineTransform): # type: ignore
                        default = tuple(default.transformStruct())
                        arg += ": Transform"
                    elif isinstance(default, AppKit.CIColor):
                        default = default.red(), default.green(), default.blue(), default.alpha()
                        arg += ": RGBColor"
                    elif isinstance(default, AppKit.NSData):
                        default = None
                        arg += ": bytes | None"
                    elif isinstance(default, type(Quartz.CGColorSpaceCreateDeviceCMYK())):
                        default = None
                    else:
                        arg += ": float"
                        if default == "None":
                            arg += " | None"
                    arg += f" = {default}"

                if filterName in degreesAngleFilterNames:
                    value = inputKey
                else:
                    value = converters.get(inputKey, inputKey).format(inputKey=inputKey)
                docValue = variableValues.get(inputKey, "a float")
                attributes[inputKey] = value

                doc.add(f"`{inputKey}` {docValue}. {pythonifyDescription(description)}")
                args.append(arg)
            doc.dedent()

        code.add(f"def {camelCase(filterName[2:])}" + (f"(self, {', '.join(args)}):" if args else f"(self):"))
        code.indent()
        code.add("\"\"\"")
        code.appendCode(doc)
        code.add("\"\"\"")
        code.appendCode(inputCode)
        filterDict = dict(name=f"'{filterName}'", attributes=attributes)
        if filterName in generators:
            filterDict["size"] = 'size'
            filterDict["isGenerator"] = 'True'
        if filterName.endswith("CodeGenerator"):
            filterDict["fitImage"] = 'True'

        code.addDict('filterDict', filterDict)

        code.add("self._addFilter(filterDict)")
        code.dedent()
        code.add("")

    imageObjectPath = Path(Path(__file__).parent.parent / "drawBot/context/tools/imageObject.py")
    imageObjectText = imageObjectPath.read_text()

    beforeFilters = []
    for eachLine in imageObjectText.splitlines():
        beforeFilters.append(eachLine)
        if eachLine == "    # --- filters ---":
            break

    with open(imageObjectPath, mode='w') as txtFile:
        txtFile.write("\n".join(beforeFilters) + "\n" + str(code))
