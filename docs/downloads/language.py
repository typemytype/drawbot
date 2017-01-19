# a long dutch word
word = "paardenkop"
# a box where we draw in
box = (10, 10, 100, 100)

# set font size
fontSize(28)
# enable hyphenation
hyphenation(True)
# draw the text with no language set
textBox(word, box)
# set language to dutch (nl)
language("nl")
# shift up a bit
translate(0, 150)
# darw the text again with a language set
textBox(word, box)