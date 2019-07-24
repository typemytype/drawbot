Text Properties
===============

.. autofunction:: drawBot.font
.. autofunction:: drawBot.fontSize
.. autofunction:: drawBot.fallbackFont
.. autofunction:: drawBot.hyphenation
.. autofunction:: drawBot.lineHeight
.. autofunction:: drawBot.tracking
.. autofunction:: drawBot.baselineShift
.. autofunction:: drawBot.openTypeFeatures(frac=True, case=True, ...)
.. autofunction:: drawBot.listOpenTypeFeatures
.. autofunction:: drawBot.fontVariations(wdth=0.6, wght=0.1, ...)
.. autofunction:: drawBot.listFontVariations
.. autofunction:: drawBot.listNamedInstances
.. autofunction:: drawBot.tabs
.. autofunction:: drawBot.language

Font Properties
---------------

.. autofunction:: drawBot.fontContainsCharacters
.. autofunction:: drawBot.fontContainsGlyph
.. autofunction:: drawBot.fontFilePath
.. autofunction:: drawBot.listFontGlyphNames
.. autofunction:: drawBot.fontDescender
.. autofunction:: drawBot.fontAscender
.. autofunction:: drawBot.fontXHeight
.. autofunction:: drawBot.fontCapHeight
.. autofunction:: drawBot.fontLeading
.. autofunction:: drawBot.fontLineHeight

.. downloadcode:: fontMetrics.py

    txt = "Hello World"
    x, y = 10, 100

    # set a font
    font("Helvetica")
    # set a font size
    fontSize(100)
    # draw the text
    text(txt, (x, y))

    # calculate the size of the text
    textWidth, textHeight = textSize(txt)

    # set a red stroke color
    stroke(1, 0, 0)
    # loop over all font metrics
    for metric in (0, fontDescender(), fontAscender(), fontXHeight(), fontCapHeight()):
        # draw a red line with the size of the drawn text
        line((x, y+metric), (x+textWidth, y+metric))

