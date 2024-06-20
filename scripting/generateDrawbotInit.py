"""
We need to "physically" write the names of the functions/methods that are exposed
with the drawBot module to allow static analysis by tools like mypy or pyright
to leverage the hints we have in the interfaces

"""

from pathlib import Path
from drawBot.context.tools import drawBotbuiltins
from drawBot import _drawBotDrawingTool

if __name__ == '__main__':
    code = []
    for name in _drawBotDrawingTool.__all__:
        if name.startswith("_"):
            continue
        code.append(f"{name} = _drawBotDrawingTool.{name}")

    code.append("")
    code.append("# directly import FormattedString, BezierPath, and ImageObject as classes")
    code.append("from drawBot.context.baseContext import FormattedString, BezierPath")
    code.append("from drawBot.context.tools.imageObject import ImageObject")

    code.append("")
    code.append("from drawBot.context.tools import drawBotbuiltins")
    for name in dir(drawBotbuiltins):
        if name.startswith("_"):
            continue
        code.append(f"{name} = drawBotbuiltins.{name}")

    initPath = Path(
        Path(__file__).parent.parent / "drawBot/__init__.py"
    )
    initText = initPath.read_text()
    before = []
    for eachLine in initText.splitlines():
        before.append(eachLine)
        if eachLine == "# --- section automatically generated --- #":
            break

    with open(initPath, mode="w") as txtFile:
        txtFile.write("\n".join(before) + "\n" + "\n".join(code))
