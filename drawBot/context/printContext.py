from baseContext import BaseContext


class PrintContext(BaseContext):

    fileExtensions = ["*"]

    def _newPage(self, width, height):
        print "newPage", width, height

    def _save(self):
        print "save"

    def _restore(self):
        print "restore"

    def _blendMode(self, operation):
        print "blend mode", operation

    def _drawPath(self):
        print "drawPath", self._state.path

    def _clipPath(self):
        print "clipPath", self._state.path

    def _transform(self, matrix):
        print "transform", matrix

    def _textBox(self, txt, (x, y, w, h), align):
        print "textBox", txt, (x, y, w, h), align

    def _image(self, path, (x, y), alpha, pageNumber):
        print "image", path, x, y, alpha, pageNumber

    def _frameDuration(self, seconds):
        print "frameDuration", seconds

    def _reset(self):
        print "reset"

    def _saveImage(self, path, multipage):
        print "saveImage", path, multipage

    def _printImage(self, pdf=None):
        print "printImage", path, multipage

    def _linkDestination(self, name, (x, y)):
        print "linkDestination", name, (x, y)

    def _linkRect(self, name, (x, y, w, h)):
        print "linkRect", name, (x, y, w, h)