# Number to String Conversion

def valueToString(v):
    """
    >>> valueToString(0)
    '0'
    >>> valueToString(10)
    '10'
    >>> valueToString(-10)
    '-10'
    >>> valueToString(0.1)
    '0.1'
    >>> valueToString(0.0001)
    '0.0001'
    >>> valueToString(0.00001)
    '0'
    >>> valueToString(10.0001)
    '10.0001'
    >>> valueToString(10.00001)
    '10'
    """
    if int(v) == v:
        v = "%d" % (int(v))
    else:
        v = "%.4f" % v
        # strip unnecessary zeros
        # there is probably an easier way to do this
        compiled = []
        for c in reversed(v):
            if not compiled and c == "0":
                continue
            compiled.append(c)
        v = "".join(reversed(compiled))
        if v.endswith("."):
            v = v[:-1]
        if not v:
            v = "0"
    return v

def pointToString(pt):
    return " ".join([valueToString(i) for i in pt])


if __name__ == "__main__":
    import doctest
    doctest.testmod()