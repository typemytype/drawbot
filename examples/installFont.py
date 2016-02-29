# set the path to a font file
path = "path/to/font/file.otf"
# install the font
fontName = installFont(path)
# set the font 
font(fontName, 200)
# draw some text
text("Hello World", (10, 10))
# uninstall font
uninstallFont(path)




