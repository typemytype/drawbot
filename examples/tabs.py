t = " hello w o r l d"
# replace all spaces by tabs
t = t.replace(" ", "\t")
# set some tabs
tabs((85, "center"), (232, "right"), (300, "left"))
# draw the string
text(t, (10, 10))
# reset all tabs
tabs(None)
# draw the same string
text(t, (10, 50))

