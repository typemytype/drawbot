from xml.etree.ElementTree import Element

def writeHKernElements(font, svgFont, ignoreGlyphs=[]):
    # flatten
    kerning = _flattenKerning(font.kerning, font.groups)
    # remove ignored glyphs
    for (l, r) in kerning.keys():
        if l in ignoreGlyphs or r in ignoreGlyphs:
            del kerning[l, r]
    # compress
    kerning = _compressKerningPhase1(kerning)
    kerning = _compressKerningPhase2(kerning)
    # normalize
    kerning = _normalizeKerning(kerning)
    # write
    for pair, value in sorted(kerning.items()):
        kern = _makeHkern(pair, value, font)
        svgFont.append(kern)

def _makeHkern(pair, value, font):
    """
    >>> font = _makeTestFont()

    # unicode characters
    >>> kern = _makeHkern(
    ...     (["A"], ["B"]),
    ...     -10,
    ...     font
    ... )
    >>> kern.tag, kern.attrib
    ('hkern', {'k': '10', 'u1': u'A', 'u2': u'B'})
    >>> kern = _makeHkern(
    ...     (["A", "C"], ["B", "D"]),
    ...     -10,
    ...     font
    ... )
    >>> kern.tag, kern.attrib
    ('hkern', {'k': '10', 'u1': u'A,C', 'u2': u'B,D'})

    # glyph names
    >>> kern = _makeHkern(
    ...     (["A.alt1"], ["B.alt1"]),
    ...     -10,
    ...     font
    ... )
    >>> kern.tag, kern.attrib
    ('hkern', {'k': '10', 'g2': 'B.alt1', 'g1': 'A.alt1'})
    >>> kern = _makeHkern(
    ...     (["A.alt1", "A.alt2"], ["B.alt1", "B.alt2"]),
    ...     -10,
    ...     font
    ... )
    >>> kern.tag, kern.attrib
    ('hkern', {'k': '10', 'g2': 'B.alt1,B.alt2', 'g1': 'A.alt1,A.alt2'})

    # mix
    >>> kern = _makeHkern(
    ...     (["A"], ["B.alt1"]),
    ...     -10,
    ...     font
    ... )
    >>> kern.tag, kern.attrib
    ('hkern', {'k': '10', 'u1': u'A', 'g2': 'B.alt1'})
    >>> kern = _makeHkern(
    ...     (["A.alt1"], ["B"]),
    ...     -10,
    ...     font
    ... )
    >>> kern.tag, kern.attrib
    ('hkern', {'k': '10', 'g1': 'A.alt1', 'u2': u'B'})
    >>> kern = _makeHkern(
    ...     (["A", "A.alt1"], ["B", "B.alt1"]),
    ...     -10,
    ...     font
    ... )
    >>> kern.tag, kern.attrib
    ('hkern', {'k': '10', 'u1': u'A', 'g2': 'B.alt1', 'g1': 'A.alt1', 'u2': u'B'})
    """
    glyph1List, glyph2List = pair
    u1 = []
    g1 = []
    for name in glyph1List:
        glyph = font[name]
        if glyph.unicode:
            u1.append(unichr(glyph.unicode))
        else:
            g1.append(name)
    u2 = []
    g2 = []
    for name in glyph2List:
        glyph = font[name]
        if glyph.unicode:
            u2.append(unichr(glyph.unicode))
        else:
            g2.append(name)
    pairAttrib = dict(k=str(-value))
    if u1:
        pairAttrib["u1"] = u",".join(u1)
    if g1:
        pairAttrib["g1"] = ",".join(g1)
    if u2:
        pairAttrib["u2"] = u",".join(u2)
    if g2:
        pairAttrib["g2"] = ",".join(g2)
    kern = Element("hkern", attrib=pairAttrib)
    return kern

# --------------------------
# Flattening and Compression
# --------------------------

def _flattenKerning(pairs, groups):
    """
    >>> kerning = {
    ...     ("@LEFT_A", "@RIGHT_A") : -25,  # group, group
    ...     ("@LEFT_A", "Agrave") : -75,    # group, glyph (excpetion to @LEFT_A, @RIGHT_A)
    ...     ("@LEFT_A", "Aacute") : -74,    # group, glyph (excpetion to @LEFT_A, @RIGHT_A)
    ...     ("Agrave", "Agrave") : -100,    # glyph, glyph (exception to @LEFT_A, Agrave)
    ...     ("@LEFT_D", "@RIGHT_D") : 25,   # group, group
    ...     ("Dcroat", "@RIGHT_D") : 75,    # glyph, group (exception to @LEFT_D, @RIGHT_D)
    ...     ("Eth", "@RIGHT_D") : 74,       # glyph, group (exception to @LEFT_D, @RIGHT_D)
    ...     ("Dcroat", "Dcroat") : 100,     # glyph, glyph (excpetion to Dcroat, @RIGHT_D)
    ...     ("@LEFT_D", "X") : -25,         # group, glyph
    ...     ("X", "@RIGHT_D") : -25,        # glyph, group
    ... }
    >>> groups = {
    ...     "@LEFT_A" : ["A", "Aacute", "Agrave"],
    ...     "@RIGHT_A" : ["A", "Aacute", "Agrave"],
    ...     "@LEFT_D" : ["D", "Dcroat", "Eth"],
    ...     "@RIGHT_D" : ["D", "Dcroat", "Eth"],
    ... }
    >>> flattened = _flattenKerning(kerning, groups)
    >>> expected = {
    ...     # from ("@LEFT_A", "@RIGHT_A") : -25
    ...     ("A", "A") : -25,
    ...     ("Aacute", "A") : -25,
    ...     ("Agrave", "A") : -25,
    ...     # from ("@LEFT_A", "Agrave") : -75,
    ...     ("A", "Agrave") : -75,
    ...     ("Aacute", "Agrave") : -75,
    ...     # from ("@LEFT_A", "Aacute") : -74
    ...     ("A", "Aacute") : -74,
    ...     ("Aacute", "Aacute") : -74,
    ...     ("Agrave", "Aacute") : -74,
    ...     # from (Agrave, Agrave) : -100
    ...     ("Agrave", "Agrave") : -100,
    ...     # from ("@LEFT_D", "@RIGHT_D") : 25,
    ...     ("D", "D") : 25,
    ...     ("D", "Dcroat") : 25,
    ...     ("D", "Eth") : 25,
    ...     # from ("Dcroat", "@RIGHT_D") : 75,
    ...     ("Dcroat", "D") : 75,
    ...     ("Dcroat", "Eth") : 75,
    ...     # from ("Eth", "@RIGHT_D") : 74,
    ...     ("Eth", "D") : 74,
    ...     ("Eth", "Dcroat") : 74,
    ...     ("Eth", "Eth") : 74,
    ...     # from ("Dcroat", "Dcroat") : 100,
    ...     ("Dcroat", "Dcroat") : 100,
    ...     # from ("@LEFT_D", "X") : -25,
    ...     ("D", "X") : -25,
    ...     ("Dcroat", "X") : -25,
    ...     ("Eth", "X") : -25,
    ...     # from ("X", "@RIGHT_D") : -25,
    ...     ("X", "D") : -25,
    ...     ("X", "Dcroat") : -25,
    ...     ("X", "Eth") : -25,
    ... }
    >>> flattened == expected
    True
    """
    # Organize the pairs into sets based on the
    # presence or absence of groups.
    glyphGlyph = {}
    groupGlyph = {}
    glyphGroup = {}
    groupGroup = {}
    for (left, right), value in pairs.items():
        if left in groups and right in groups:
            d = groupGroup
        elif left in groups:
            d = groupGlyph
        elif right in groups:
            d = glyphGroup
        else:
            d = glyphGlyph
        d[left, right] = value
    # Start with the glyph, glyph pairs since
    # they can't be flattened any further.
    flattened = dict(glyphGlyph)
    # Flatten group, glyph
    for (left, right), value in groupGlyph.items():
        # The left is a group, so work through
        # all group members plus the right.
        for l in groups[left]:
            # If the pair is already flattened, skip it.
            if (l, right) in flattened:
                continue
            flattened[l, right] = value
    # Flatten glyph, group
    for (left, right), value in glyphGroup.items():
        # The right is a group, so work through
        # all group members plus the left.
        for r in groups[right]:
            # If the pair is already flattened, skip it.
            if (left, r) in flattened:
                continue
            flattened[left, r] = value
    # Flatten group, group
    for (left, right), value in groupGroup.items():
        # Work through the left group.
        for l in groups[left]:
            # Work through the right group.
            for r in groups[right]:
                # If the pair is already flattened, skip it.
                if (l, r) in flattened:
                    continue
                flattened[l, r] = value
    # Done.
    return flattened

def _compressKerningPhase1(kerning):
    """
    >>> kerning = {
    ...     ("A", "A") : 100,
    ...     ("A", "Aacute") : 100,
    ...     ("Aacute", "A") : 100,
    ...     ("A", "Agrave") : 200,
    ...     ("Agrave", "A") : 200,
    ...     ("A", "Adieresis") : 300,
    ... }
    >>> expected = {
    ...     ("A", 100) : set(["A", "Aacute"]),
    ...     ("Aacute", 100) : set(["A"]),
    ...     ("A", 200) : set(["Agrave"]),
    ...     ("Agrave", 200) : set(["A"]),
    ...     ("A", 300) : set(["Adieresis"]),
    ... }
    >>> result = _compressKerningPhase1(kerning)
    >>> result == expected
    True
    """
    # create a dict of form {(glyph1, value) : set(glyph2s)}
    compressed = {}
    for (glyph1, glyph2), value in kerning.items():
        k = (glyph1, value)
        if k not in compressed:
            compressed[k] = set()
        compressed[k].add(glyph2)
    return compressed

def _compressKerningPhase2(kerning):
    """
    >>> kerning = {
    ...     ("A", 100) : set(["A", "Aacute"]),
    ...     ("Aacute", 100) : set(["A", "Aacute"]),
    ...     ("A", 200) : set(["Agrave"]),
    ...     ("Agrave", 200) : set(["A"]),
    ...     ("A", 300) : set(["Adieresis"]),
    ... }
    >>> expected = {
    ...     (("A", "Aacute"), 100) : set(["A", "Aacute"]),
    ...     (tuple(["Agrave"]), 200) : set(["A"]),
    ...     (tuple(["A"]), 200) : set(["Agrave"]),
    ...     (tuple(["Adieresis"]), 300) : set(["A"]),
    ... }
    >>> result = _compressKerningPhase2(kerning)
    >>> result == expected
    True
    """
    # create a dict of form {(glyph2s, value) : set(glyph1s)}
    compressed = {}
    for (glyph1, value), glyph2List in kerning.items():
        k = (tuple(sorted(glyph2List)), value)
        if k not in compressed:
            compressed[k] = set()
        compressed[k].add(glyph1)
    return compressed

def _normalizeKerning(kerning):
    normalized = {}
    for (glyph2List, value), glyph1List in kerning.items():
        glyph1List = tuple(sorted(glyph1List))
        glyph2List = tuple(sorted(glyph2List))
        normalized[glyph1List, glyph2List] = value
    return normalized

# ------------
# Test Support
# ------------

def _makeTestFont():
    from fontTools.agl import AGL2UV
    from defcon import Font
    font = Font()
    for name in "ABCD":
        font.newGlyph(name)
        font.newGlyph(name + ".alt1")
        font.newGlyph(name + ".alt2")
    for glyph in font:
        glyph.unicode = AGL2UV.get(glyph.name)
    return font


if __name__ == "__main__":
    import doctest
    doctest.testmod()