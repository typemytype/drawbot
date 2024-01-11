import os
from typing import Sequence

Point = Size = tuple[float, float]
OptionalPoint = Point | None
Points = Sequence[Point]
OptionalFloat = float | None
SomePath = os.PathLike | str
CMYKColor = float | tuple[float, ...]
RGBColor = float | tuple[float, ...]
BoundingBox = tuple[float, float, float, float]
OptionalBox = BoundingBox | None
OptionalStr = str | None
OptionalInt = int | None
Transform = tuple[float, float, float, float, float, float]
