from AppKit import *

import sys

# errors
class DrawBotError(TypeError): pass

# default tools


def getDefault(key, defaultValue=None):
    """
    Get a value from the user default for a key. 
    """
    defaultsFromFile = NSUserDefaults.standardUserDefaults()
    return defaultsFromFile.get(key, defaultValue)
    
def setDefault(key, value):
    """
    Set a value to the user defaults for a given key.
    """
    defaultsFromFile = NSUserDefaults.standardUserDefaults()
    defaultsFromFile.setObject_forKey_(value, key)

def _getNSDefault(key, defaultValue=None):
    data = getDefault(key, defaultValue)
    if isinstance(data, NSData):
        return NSUnarchiver.unarchiveObjectWithData_(data)
    return data

def _setNSDefault(key, value):
    data = NSArchiver.archivedDataWithRootObject_(value)
    setDefault(key, data)

def getFontDefault(key, defaultValue=None):
    return _getNSDefault(key, defaultValue)

def setFontDefault(key, font):
    _setNSDefault(key, font)

def getColorDefault(key, defaultValue=None):
    return _getNSDefault(key, defaultValue)

def setColorDefault(key, color):
    _setNSDefault(key, color)

# color tools

def cmyk2rgb(c, m, y, k):
    """
    Convert cmyk color to rbg color.
    """
    r = 1.0 - min(1.0, c + k)
    g = 1.0 - min(1.0, m + k)
    b = 1.0 - min(1.0, y + k)
    return r, g, b

def rgb2cmyk(r, g, b):
    """
    Convert rgb color to cmyk color.
    """
    c = 1 - r
    m = 1 - g
    y = 1 - b
    k = min(c,m,y)
    c = min(1, max(0,c-k))
    m = min(1, max(0,m-k))
    y = min(1, max(0,y-k))
    k = min(1, max(0,k))
    return c, m, y, k

def stringToInt(code):
    import struct
    return struct.unpack('>l', code)[0]

class Warnings(object):

    def __init__(self):
        self._warnMessages = set()

    def resetWarnings(self):
        self._warnMessages = set()

    def warn(self, message):
        if message in self._warnMessages:
            return
        sys.stderr.write("*** DrawBot warning: %s ***\n" % message)
        self._warnMessages.add(message)

warnings = Warnings()
