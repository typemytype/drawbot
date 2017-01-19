# create small ui element for variables in the script

Variable([
    # create a variable called 'w'
    # and the related ui is a Slider.
    dict(name="w", ui="Slider"),
    # create a variable called 'h'
    # and the related ui is a Slider.
    dict(name="h", ui="Slider",
            args=dict(
                # some vanilla specific
                # setting for a slider
                value=100,
                minValue=50,
                maxValue=300)),
    # create a variable called 'useColor'
    # and the related ui is a CheckBox.
    dict(name="useColor", ui="CheckBox"),
    # create a variable called 'c'
    # and the related ui is a ColorWell.
    dict(name="c", ui="ColorWell")
    ], globals())

# draw a rect
rect(0, 0, w, h)

# check if the 'useColor' variable is checked
if useColor:
    # set the fill color from the variables
    fill(c)
# set the font size
fontSize(h)
# draw some text
text("Hello Variable", (w, h))