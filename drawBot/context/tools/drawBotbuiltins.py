
def norm(value, start, stop):
    """
    Return the interpolation factor (between 0 and 1) of a VALUE between START and STOP.
    """
    return float(value - start) / float(stop - start)


def lerp(start, stop, factor):
    """
    Interpolate using a value between 0 and 1
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
        if factor > 1:
            factor = 1
    return lerp(start2, stop2, factor)
