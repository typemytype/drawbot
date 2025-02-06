import os
from typing import Sequence

Size = tuple[int, int]
Point = tuple[float, float]
Points = Sequence[Point]
SomePath = os.PathLike | str
CMYKColor = float | tuple[float, ...]
RGBAColorTuple = tuple[float, float, float, float]
CMYKColorTuple = tuple[float, float, float, float]
RGBColorTuple = tuple[float, float, float]
RGBColor = float | tuple[float, ...]
BoundingBox = tuple[float, float, float, float]
TransformTuple = tuple[float, float, float, float, float, float]
