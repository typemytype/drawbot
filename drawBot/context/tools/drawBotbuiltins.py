
def norm(value, start, stop):
    """
    Return the interpolation factor (between 0 and 1) of a `value` between `start` and `stop`.
    """
    return (value - start) / (stop - start)


def lerp(start, stop, factor):
    """
    Return an interpolated value between `start` and `stop` using interpolation factor `factor`.
    """
    return start + (stop - start) * factor


def remap(value, start1, stop1, start2, stop2, clamp=False):
    """
    Re-maps a number from one range to another.
    """
    factor = norm(value, start1, stop1)
    if clamp:
        if factor < 0:
            factor = 0
        elif factor > 1:
            factor = 1
    return lerp(start2, stop2, factor)
