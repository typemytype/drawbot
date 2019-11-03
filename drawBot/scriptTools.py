import AppKit
import time
import os
import sys
import traceback
import re
import warnings
from signal import SIGINT
import ctypes
from ctypes.util import find_library
import threading
from .misc import getDefault
from .macOSVersion import macOSVersion
from objc import super


# Pulling in CheckEventQueueForUserCancel from Carbon.framework
CheckEventQueueForUserCancel = None

def retrieveCheckEventQueueForUserCancelFromCarbon():
    # call this function explicit from the app didFinishLaunching
    global CheckEventQueueForUserCancel
    _carbonPath = find_library("Carbon")
    if _carbonPath is not None:
        CheckEventQueueForUserCancel = ctypes.CFUNCTYPE(ctypes.c_bool)(('CheckEventQueueForUserCancel', ctypes.CDLL(_carbonPath)))
    else:
        from drawBot.misc import warnings
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
        # get all warnings
        warnFilters = list(warnings.filters)
        # reset warnings
        warnings.resetwarnings()
        # ignore all warnings
        # we dont want warnings while pusing text to the textview
        warnings.filterwarnings("ignore")
        if self.outputView is not None:
            # Better not get SIGINT/KeyboardInterrupt exceptions while we're updating the output view
            with cancelLock:
                self.outputView.append(data, self.isError)
                t = time.time()
                if t - self._previousFlush > 0.2:
                    self.outputView.scrollToEnd()
                    if macOSVersion >= "10.10":
                        AppKit.NSRunLoop.mainRunLoop().runUntilDate_(AppKit.NSDate.dateWithTimeIntervalSinceNow_(0.0001))
                    self._previousFlush = t
        else:
            self.data.append((data, self.isError))
        # reset the new warnings
        warnings.resetwarnings()
        # update with the old warnings filters
        warnings.filters.extend(warnFilters)

    def flush(self):
        pass

    def close(self):
        pass


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
        with open(path, 'rb') as f:
            text = f.read().decode("utf-8")
    source = text.replace('\r\n', '\n').replace('\r', '\n')
    compileFlags = 0

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
