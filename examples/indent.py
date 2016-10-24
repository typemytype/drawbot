# setting up some variables
x, y, w, h = 10, 10, 200, 300

txtIndent = 50
txtFirstLineIndent = 70
txtTailIndent = -50

paragraphTop = 3
paragraphBottom = 10

txt = """DrawBot is an ideal tool to teach the basics of programming. Students get colorful graphic treats while getting familiar with variables, conditional statements, functions and what have you. Results can be saved in a selection of different file formats, including as high resolution, scaleable PDF, svg, movie, png, jpeg, tiff..."""

# a new page with preset size
newPage(w+x*2, h+y*2)
# draw text indent line
stroke(1, 0, 0)
line((x+txtIndent, y), (x+txtIndent, y+h))
# draw text firstline indent line
stroke(1, 1, 0)
line((x+txtFirstLineIndent, y), (x+txtFirstLineIndent, y+h))
# draw tail indent
pos = txtTailIndent
# tail indent could be negative
if pos <= 0:
    # substract from width of the text box
    pos = w + pos
stroke(0, 0, 1)
line((x+pos, y), (x+pos, y+h))
# draw a rectangle 
fill(0, .1)
stroke(None)
rect(x, y, w, h)

# create a formatted string
t = FormattedString()
# set alignment
t.align("justified")
# add text
t += txt
# add hard return
t += "\n"
# set style for indented text
t.fontSize(6)
t.paragraphTopSpacing(paragraphTop)
t.paragraphBottomSpacing(paragraphBottom)
t.firstLineIndent(txtFirstLineIndent)
t.indent(txtIndent)
t.tailIndent(txtTailIndent)
# add text
t += txt
# add hard return
t += "\n"
# reset style
t.fontSize(10)
t.indent(None)
t.tailIndent(None)
t.firstLineIndent(None)
t.paragraphTopSpacing(None)
t.paragraphBottomSpacing(None)
# add text
t += txt
# draw formatted string in a text box
textBox(t, (x, y, w, h))



