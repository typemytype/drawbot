from __future__ import division, absolute_import

# -*- coding: UTF-8 -*-
import __future__
import AppKit
import time
import os
import sys
import traceback
import site
import re

from vanilla.vanillaBase import osVersion10_10, osVersionCurrent

from fontTools.misc.py23 import PY2, PY3

from drawBot.misc import getDefault, executeExternalProcess


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
            self.outputView.append(data, self.isError)
            # self.outputView.forceUpdate()
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


class DrawBotNamespace(dict):

    def __init__(self, context, variables):
        self._context = context
        self._variables = variables

    def __getitem__(self, item):
        if item in self._variables:
            return getattr(self._context, item)
        return super(DrawBotNamespace, self).__getitem__(item)


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


class ScriptRunner(object):

    def __init__(self, text=None, path=None, stdout=None, stderr=None, namespace=None, checkSyntaxOnly=False):
        from threading import Thread
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

        if stdout:
            sys.stdout = stdout
        if stderr:
            sys.stderr = stderr
        sys.argv = [fileName]
        os.chdir(curDir)
        sys.path.insert(0, curDir)
        # here we go
        if text is None:
            f = open(path, 'rb')
            text = f.read()
            f.close()
        source = text.replace('\r\n', '\n').replace('\r', '\n')
        if PY2 and hasEncodingDeclaration(source):
            # Python 2 compile() complains when an encoding declaration is found in a unicode string.
            # As a workaround, we'll just encode it back as a utf-8 string and all is good.
            try:
                source = source.encode("utf-8")
            except:
                pass
        compileFlags = 0
        if getDefault("DrawBotUseFutureDivision", True):
            compileFlags |= __future__.CO_FUTURE_DIVISION

        try:
            try:
                code = compile(source + '\n\n', fileName, "exec", compileFlags)
            except:
                traceback.print_exc(0)
            else:
                if not checkSyntaxOnly:
                    self._scriptDone = False
                    try:
                        exec(code, namespace)
                    except KeyboardInterrupt:
                        pass
                    except:
                        etype, value, tb = sys.exc_info()
                        if tb.tb_next is not None:
                            tb = tb.tb_next
                        traceback.print_exception(etype, value, tb)
                        etype = value = tb = None
        finally:
            # reset the important bits
            self._scriptDone = True
            sys.stdout = saveStdout
            sys.stderr = saveStderr
            sys.argv = saveArgv
            if saveDir:
                os.chdir(saveDir)
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
