# create a new formatted string
t = FormattedString()
# set some tabs
t.tabs((85, "center"), (232, "right"), (300, "left"))
# add text with tabs
t += " hello w o r l d".replace(" ", "\t")
# draw the string
text(t, (10, 10))