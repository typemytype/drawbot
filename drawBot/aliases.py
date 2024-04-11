import os
from typing import Sequence

Point = Size = tuple[float, float]
Points = Sequence[Point]
SomePath = os.PathLike | str
CMYKColor = float | tuple[float, ...]
RGBColor = float | tuple[float, ...]
BoundingBox = tuple[float, float, float, float]
Transform = tuple[float, float, float, float, float, float]
