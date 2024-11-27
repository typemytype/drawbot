"""
We need to "physically" write the names of the functions/methods that are exposed
with the drawBot module to allow static analysis by tools like mypy or pyright
to leverage the hints we have in the interfaces

"""

from drawBot.context.tools import drawBotbuiltins
from drawBot import _drawBotDrawingTool
from pathlib import Path

INIT_PATH = Path(__file__).parent.parent / "drawBot/__init__.py"

def generateInitCode():
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

    initText = INIT_PATH.read_text()
    before = []
    for eachLine in initText.splitlines():
        before.append(eachLine)
        if eachLine == "# --- section automatically generated --- #":
            break

    return "\n".join(before) + "\n" + "\n".join(code)

if __name__ == '__main__':
    initCode = generateInitCode()
    INIT_PATH.write_text(initCode)
