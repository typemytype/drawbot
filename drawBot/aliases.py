import os
from typing import Sequence

Size = tuple[float, float]
Point = tuple[float, float]
Points = Sequence[Point]
SomePath = os.PathLike | str
CMYKColor = float | tuple[float, ...]
# used for output values which are always 4 elements
RGBAColorTuple = tuple[float, float, float, float]
RGBColor = float | tuple[float, ...]
BoundingBox = tuple[float, float, float, float]
TransformTuple = tuple[float, float, float, float, float, float]
