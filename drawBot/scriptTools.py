from __future__ import division, absolute_import, print_function

# -*- coding: UTF-8 -*-
import __future__
import AppKit
import time
import os
import sys
import traceback
import site
import re
from signal import SIGINT
import ctypes
from ctypes.util import find_library
import threading
from distutils.version import StrictVersion
import platform
from fontTools.misc.py23 import PY2, PY3
from drawBot.misc import getDefault, warnings


osVersionCurrent = StrictVersion(platform.mac_ver()[0])
osVersion10_10 = StrictVersion("10.10")


# Pulling in CheckEventQueueForUserCancel from Carbon.framework
CheckEventQueueForUserCancel = None

def retrieveCheckEventQueueForUserCancelFromCarbon():
    # call this function explicit from the app didFinishLaunching
    global CheckEventQueueForUserCancel
    _carbonPath = find_library("Carbon")
    if _carbonPath is not None:
        CheckEventQueueForUserCancel = ctypes.CFUNCTYPE(ctypes.c_bool)(('CheckEventQueueForUserCancel', ctypes.CDLL(_carbonPath)))
    else:
        warnings.warn("Carbon.framework can't be found; command-period script cancelling will not work.")


# Acquire this lock if something must not be interrupted by command-period or escape
cancelLock = threading.Lock()


class StdOutput(object):

    def __init__(self, output, isError=False, outputView=None):
        self.data = output
        self.isError = isError
        self.outputView = outputView
        self._previousFlush = time.time()

    def write(self, data):
        if PY2 and isinstance(data, str):
            try:
                data = unicode(data, "utf-8", "replace")
            except UnicodeDecodeError:
                data = "XXX " + repr(data)
        if self.outputView is not None:
            # Better not get SIGINT/KeyboardInterrupt exceptions while we're updating the output view
            with cancelLock:
                self.outputView.append(data, self.isError)
                t = time.time()
                if t - self._previousFlush > 0.2:
                    self.outputView.scrollToEnd()
                    if osVersionCurrent >= osVersion10_10:
                        AppKit.NSRunLoop.mainRunLoop().runUntilDate_(AppKit.NSDate.dateWithTimeIntervalSinceNow_(0.0001))
                    self._previousFlush = t
        else:
            self.data.append((data, self.isError))

    def flush(self):
        pass

    def close(self):
        pass


def _addLocalSysPaths():
    version = "%s.%s" % (sys.version_info.major, sys.version_info.minor)
    if PY3:
        paths = [
            # add local stdlib and site-packages; TODO: this needs editing once we embed the full stdlib
            '/Library/Frameworks/Python.framework/Versions/%s/lib/python%s' % (version, version),
            '/Library/Frameworks/Python.framework/Versions/%s/lib/python%s/lib-dynload' % (version, version),
            '/Library/Frameworks/Python.framework/Versions/%s/lib/python%s/site-packages' % (version, version),
        ]
    else:
        paths = [
            '/System/Library/Frameworks/Python.framework/Versions/%s/lib/python%s' % (version, version),
            '/System/Library/Frameworks/Python.framework/Versions/%s/lib/python%s/lib-dynload' % (version, version),
            '/System/Library/Frameworks/Python.framework/Versions/%s/lib/python%s/site-packages' % (version, version),
        ]

    paths.append('/Library/Python/%s/site-packages' % version)

    for path in paths:
        if path not in sys.path and os.path.exists(path):
            site.addsitedir(path)

_addLocalSysPaths()


class _Helper(object):
    """
    Define the builtin 'help'.
    This is a wrapper around pydoc.help (with a twist).
    """

    def __repr__(self):
        return "Type help() for interactive help, " \
               "or help(object) for help about object."

    def __call__(self, *args, **kwds):
        import pydoc
        return pydoc.help(*args, **kwds)


# Regex taken from http://legacy.python.org/dev/peps/pep-0263/
_encodingDeclarationPattern = re.compile(r"^[ \t\v]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")

def hasEncodingDeclaration(source):
    # An encoding declaration must occur within the first two lines of the source code
    if _encodingDeclarationPattern.match(source) is not None:
        return True
    pos = source.find("\n")
    if pos >= 0:
        if _encodingDeclarationPattern.match(source[pos+1:]) is not None:
            return True
    return False


def ScriptRunner(text=None, path=None, stdout=None, stderr=None, namespace=None, checkSyntaxOnly=False):

    def userCancelledMonitor():
        # This will be called from a thread
        while not scriptDone:  # scriptDone is in the surrounding scope
            if CheckEventQueueForUserCancel():
                # Send a SIGINT signal to ourselves.
                # This gets delivered to the main thread as a KeyboardInterrupt
                # exception, cancelling the running script.
                with cancelLock:
                    os.kill(os.getpid(), SIGINT)
                break
            time.sleep(0.25)  # check at most 4 times per second

    if path:
        if PY2 and isinstance(path, unicode):
            path = path.encode("utf-8")
        curDir, fileName = os.path.split(path)
    else:
        curDir = os.getenv("HOME")
        fileName = '<untitled>'
    # save up the important bits
    saveStdout = sys.stdout
    saveStderr = sys.stderr
    saveArgv = sys.argv
    try:
        saveDir = os.getcwd()
    except:
        saveDir = None
    # set up the name space
    if namespace is None:
        namespace = dict()
    namespace["__file__"] = path
    namespace["__name__"] = "__main__"
    namespace["help"] = _Helper()

    if stdout is not None:
        sys.stdout = stdout
    if stderr is not None:
        sys.stderr = stderr
    sys.argv = [fileName]
    if curDir:
        os.chdir(curDir)
        sys.path.insert(0, curDir)
    # here we go
    if text is None:
        with open(path, 'r') as f:
            text = f.read()
    source = text.replace('\r\n', '\n').replace('\r', '\n')
    if PY2 and hasEncodingDeclaration(source) and isinstance(source, unicode):
        # Python 2 compile() complains when an encoding declaration is found in a unicode string.
        # As a workaround, we'll just encode it back as a utf-8 string and all is good.
        source = source.encode("utf-8")
    compileFlags = 0
    if getDefault("DrawBotUseFutureDivision", True):
        compileFlags |= __future__.CO_FUTURE_DIVISION

    try:
        try:
            code = compile(source + '\n\n', fileName, "exec", compileFlags, dont_inherit=True)
        except:
            traceback.print_exc(0)
        else:
            if not checkSyntaxOnly:
                scriptDone = False
                if CheckEventQueueForUserCancel is not None:
                    t = threading.Thread(target=userCancelledMonitor, name="UserCancelledMonitor")
                    t.start()
                try:
                    exec(code, namespace)
                except KeyboardInterrupt:
                    sys.stderr.write("Cancelled.\n")
                except:
                    etype, value, tb = sys.exc_info()
                    if tb.tb_next is not None:
                        tb = tb.tb_next
                    traceback.print_exception(etype, value, tb)
                    etype = value = tb = None
    finally:
        # reset the important bits
        scriptDone = True
        sys.stdout = saveStdout
        sys.stderr = saveStderr
        sys.argv = saveArgv
        if saveDir:
            os.chdir(saveDir)
        if curDir:
            sys.path.remove(curDir)


def CallbackRunner(callback, stdout=None, stderr=None, args=[], kwargs={}, fallbackResult=None):
    result = fallbackResult
    saveStdout = sys.stdout
    saveStderr = sys.stderr
    if stdout:
        sys.stdout = stdout
    if stderr:
        sys.stderr = stderr
    try:
        result = callback(*args, **kwargs)
    except:
        etype, value, tb = sys.exc_info()
        if tb.tb_next is not None:
            tb = tb.tb_next
        traceback.print_exception(etype, value, tb)
        etype = value = tb = None
    finally:
        sys.stdout = saveStdout
        sys.stderr = saveStderr

    return result
