from baseContext import BaseContext


class PrintContext(BaseContext):

    fileExtensions = ["*"]

    def _newPage(self, width, height):
        print "newPage", width, height

    def _saveImage(self, paths, multipage):
        print "saveImage", paths, multipage

    def _save(self):
        print "save"

    def _restore(self):
        print "restore"

    def _blendMode(self, operation):
        print "blend mode", operation

    def _drawPath(self):
        print "drawPath", self._state.path

    def _transform(self, matrix):
        print "transform", matrix

    def _textBox(self, txt, (x, y, w, h), align):
        print "textBox", txt, (x, y, w, h), align

    def _image(self, path, (x, y), alpha, pageNumber):
        print "image", path, x, y, alpha, pageNumber

    def _frameDuration(self, seconds):
        print "frameDuration", seconds
