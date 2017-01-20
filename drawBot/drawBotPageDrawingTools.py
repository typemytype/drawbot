from drawBotDrawingTools import _drawBotDrawingTool, DrawBotError, DrawBotDrawingTool


class DrawBotDrawingToolPage(DrawBotDrawingTool):

    def __init__(self, instructionSet):
        super(DrawBotDrawingToolPage, self).__init__()
        # add the instruction set
        self._instructionsStack.append(instructionSet)
        # draw all instructions into it self
        # just to set all attributes into the dummycontext
        # this is important for the current state
        self._drawInContext(self)

    def _addInstruction(self, callback, *args, **kwargs):
        # dont add any instructions
        pass


class DrawBotPage(object):

    def __init__(self, instructionSet):
        self._instructionSet = instructionSet

    def __enter__(self):
        # copy/save a state of the existing drawing tool
        self._originalTool = _drawBotDrawingTool._copy()
        # overwrite the globals newPage and size
        globals()["newPage"] = self._newPage
        globals()["size"] = self._size
        # load the instructions
        pageTool = DrawBotDrawingToolPage(self._instructionSet)
        # reset the existing one, with the page tool
        _drawBotDrawingTool._reset(pageTool)
        return self

    def __exit__(self, type, value, traceback):
        # reset the main drawing tool with a saved state of the tool
        _drawBotDrawingTool._reset(self._originalTool)
        # reset the globals newPage and size
        globals()["newPage"] = _drawBotDrawingTool.newPage
        globals()["size"] = _drawBotDrawingTool.size

    def _newPage(self, width, height=None):
        # dont allow to add a page
        raise DrawBotError("A Page cannot add a 'newPage'")

    def _size(self, width, height=None):
        # dont allow to set a page size
        raise DrawBotError("A Page cannot set a 'size'")
