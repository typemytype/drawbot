size("A4")

# make the page DIN A4 with a small inset
inset = 10
tframe = (inset,inset,width()-2*inset, height()-2*inset)


def getAllFontsWithAttributes():
    result = {}
    fonts = installedFonts()
    for font in fonts:
        l = listOpenTypeFeatures( font )
        
        # filter out fonts that have no or less than 3 attributes
        # size 2 fonts seem to be dlig & liga 
        if not l or len(l) <= 2:
            # it's dlig and liga - shown by default?
            continue
        result[font] = l
    return result


fonts = getAllFontsWithAttributes()
fontnames = fonts.keys()
fontnames.sort()

nl = '\n'
# s = "abcdefghijklmnopqrstuvwxyzäöü ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜß 0123456789"+nl

# this demotext highlights the differences better
s = "Hello, HELLO World! 0123456789 fl fi ffl ffi ABC abc 2.0 2.o"+nl

nameandattributeFontname = "Monaco"
fontnamesize = 10
attributesize = 8
demotextsize = 24

idx = 0
pnum = 1
for fontname in fontnames:
    idx += 1

    # each font his own string
    t = FormattedString()
    
    # font name header
    t.font( nameandattributeFontname )
    t.fontSize( fontnamesize )
    t += fontname + nl
    t.font( nameandattributeFontname )
    t.fontSize( attributesize )
    t += 'PLAIN' + nl
    
    # plain demotext
    t.font( fontname )
    t.fontSize( demotextsize)
    t.openTypeFeatures( None )
    t += s
    
    for ofattrib in fonts[fontname]:
        # type attribute name
        t.font( nameandattributeFontname )
        t.fontSize( attributesize )
        t += nl + ofattrib + nl
        t.font( fontname )
        t.fontSize( demotextsize )
        t.openTypeFeatures( **{ofattrib:1} )
        t += s
        t.openTypeFeatures( None )

    # render font and add pages if needed
    overflow = textBox(t, tframe)
    while overflow:
        newPage()
        pnum += 1
        overflow = textBox(overflow, tframe)

    if idx >= 20:
        # make this a break for debugging
        pass # break

    # prevent a last empty page
    if idx != len(fonts):
        newPage()
        pnum += 1

print pnum, "Pages."
