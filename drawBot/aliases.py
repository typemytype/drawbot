import os
from typing import Sequence

Point = tuple[float, float]
OptionalPoint = Point | None
Points = Sequence[Point]
OptionalFloat = float | None
SomePath = os.PathLike | str
CMYKColor = float | tuple[float, ...]
RGBColor = float | tuple[float, ...]
Box = tuple[float, float, float, float]
OptionalBox = Box | None
OptionalStr = str | None
OptionalInt = int | None
AffineTransformation = tuple[float, float, float, float, float, float]
