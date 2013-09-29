# -*- coding: UTF-8 -*-
import __future__
import os
import sys
import traceback
import site
import tempfile
import Quartz
import time

class StdOutput(object):

    def __init__(self, output, isError=False):
        self.data = output
        self.isError = isError

    def write(self, data):
        if isinstance(data, str):
            try:
                data = unicode(data, "utf-8", "replace")
            except UnicodeDecodeError:
                data = "XXX " + repr(data)
        self.data.append((data, self.isError))

    def flush(self):
        pass

    def close(self):
        pass

def _makeEnviron():
    env = dict(os.environ)
    kill = ["ARGVZERO", "EXECUTABLEPATH", "PYTHONHOME", "PYTHONPATH", "RESOURCEPATH"]
    for key in kill:
        if key in env:
            del env[key]
    return env

def _execute(cmds):
    import subprocess
    stderrPath = tempfile.mkstemp()[1]
    stdoutPath = tempfile.mkstemp()[1]
    stderrFile = open(stderrPath, "w")
    stdoutFile = open(stdoutPath, "w")
    # get the os.environ
    env = _makeEnviron()
    # make a string of escaped commands
    cmds = subprocess.list2cmdline(cmds)
    # go
    popen = subprocess.Popen(cmds, stderr=stderrFile, stdout=stdoutFile, env=env, shell=True)
    popen.wait()
    # get the output
    stderrFile.close()
    stdoutFile.close()
    stderrFile = open(stderrPath, "r")
    stdoutFile = open(stdoutPath, "r")
    stderr = stderrFile.read()
    stdout = stdoutFile.read()
    stderrFile.close()
    stdoutFile.close()
    # trash the temp files
    os.remove(stderrPath)
    os.remove(stdoutPath)
    # done
    return stderr, stdout

localSitePackagesCode = u"""
from distutils import sysconfig

_site_packages_path = sysconfig.get_python_lib()
print _site_packages_path
"""

def getLocalCurrentPythonVersionDirName():
    tempFile = tempfile.mkstemp(".py")[1]

    f = open(tempFile, "w")
    f.write(localSitePackagesCode)
    f.close()

    log = _execute(["python", tempFile])[1]
    
    sitePackages = log.split("\n")[0]
    
    os.remove(tempFile)
    if os.path.exists(sitePackages):
        return sitePackages
    else:
        return False

localSitePackagesPath = getLocalCurrentPythonVersionDirName()

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

class ScriptRunner(object):
    
    def __init__(self, text=None, path=None, stdout=None, stderr=None, namespace=None, checkSyntaxOnly=False):
        from threading import Thread
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
        
        if stdout:
            sys.stdout = stdout
        if stderr:
            sys.stderr = stderr
        sys.argv = [fileName]
        os.chdir(curDir)
        sys.path.insert(0, curDir)
        if localSitePackagesPath and localSitePackagesPath not in sys.path:
            site.addsitedir(localSitePackagesPath)
        # here we go
        if text is None:
            f = open(path, 'rb')
            text = f.read()
            f.close()
        source = text.replace('\r\n', '\n').replace('\r', '\n')
        userCancelID = None
        try:
            try:
                code = compile(source + '\n\n', fileName, "exec", __future__.CO_FUTURE_DIVISION)
            except:
                traceback.print_exc(0)
            else:
                if not checkSyntaxOnly:
                    self._scriptDone = False
                    try:
                        exec code in namespace
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




