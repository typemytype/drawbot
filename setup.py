from __future__ import print_function

import py2app
from distutils.core import setup
import os
import sys
import subprocess
import shutil
import datetime
from plistlib import readPlist, writePlist

from fontTools.misc.py23 import PY3

from drawBot.drawBotSettings import __version__, appName

rawTimeStamp = datetime.datetime.today()
timeStamp = rawTimeStamp.strftime("%y%m%d%H%M")


def getValueFromSysArgv(key, default=None, isBooleanFlag=False):
    if key in sys.argv:
        try:
            i = sys.argv.index(key)
            if isBooleanFlag:
                value = True
            else:
                value = sys.argv[i + 1]
                del sys.argv[i + 1]
            sys.argv.remove(key)
            return value
        except Exception:
            pass
    return default


codeSignDeveloperName = getValueFromSysArgv("--codesign")

ftpHost = getValueFromSysArgv("--ftphost")
ftpPath = getValueFromSysArgv("--ftppath")
ftpLogin = getValueFromSysArgv("--ftplogin")
ftpPassword = getValueFromSysArgv("--ftppassword")
buildDMG = getValueFromSysArgv("--dmg", isBooleanFlag=True)
runTests = getValueFromSysArgv("--runTests", isBooleanFlag=True)

osxMinVersion = "10.9.0"

if PY3:
    iconFile = "DrawBotPy3.icns"
else:
    iconFile = "DrawBot.icns"

plist = dict(

    CFBundleDocumentTypes=[
        dict(
            CFBundleTypeExtensions=["py"],
            CFBundleTypeName="Python Source File",
            CFBundleTypeRole="Editor",
            CFBundleTypeIconFile="pythonIcon.icns",
            NSDocumentClass="DrawBotDocument",
        ),
    ],
    CFBundleIdentifier="com.drawbot",
    LSMinimumSystemVersion=osxMinVersion,
    LSApplicationCategoryType="public.app-category.graphics-design",
    LSMinimumSystemVersionByArchitecture=dict(i386=osxMinVersion, x86_64=osxMinVersion),
    LSArchitecturePriority=["x86_64", "i386"],
    CFBundleShortVersionString=__version__,
    CFBundleVersion=__version__,
    CFBundleIconFile=iconFile,
    NSHumanReadableCopyright="Copyright by Just van Rossum and Frederik Berlaen.",
    CFBundleURLTypes=[
        dict(
            CFBundleURLName="com.drawbot",
            CFBundleURLSchemes=[appName.lower()])
    ],
)


dataFiles = [
    "Resources/English.lproj",
    # os.path.dirname(vanilla.__file__),
]

# add all images
for fileName in os.listdir("Resources/Images"):
    baseName, extension = os.path.splitext(fileName)
    if extension.lower() in [".png", ".icns"]:
        fullPath = os.path.join("Resources/Images", fileName)
        dataFiles.append(fullPath)

# add all external tools
for fileName in os.listdir("Resources/externalTools"):
    fullPath = os.path.join("Resources/externalTools", fileName)
    dataFiles.append(fullPath)

# build
setup(
    name=appName,
    data_files=dataFiles,
    app=[dict(script="DrawBot.py", plist=plist)],
    options=dict(
        py2app=dict(
            packages=[
                'vanilla',
                'defcon',
                'defconAppKit',
                'fontParts',
                'mutatorMath',
                'woffTools',
                'compositor',
                'feaTools2',
                'ufo2svg',
                'booleanOperations',
                # 'pyclipper',
                'pygments',
                'jedi',
                'fontTools',
                # 'xml'
                'pkg_resources',
            ],
            includes=[
                # 'csv',
                # 'this'
            ],
            excludes=[
                "numpy",
                "scipy",
                "matplotlib",
                "PIL",
                "pygame",
                "wx",
                "sphinx",
                "jinja2",
            ]
        )
    )
)

# fix the icon
path = os.path.join(os.path.dirname(__file__), "dist", "%s.app" % appName, "Contents", "Info.plist")
appPlist = readPlist(path)
appPlist["CFBundleIconFile"] = iconFile
writePlist(appPlist, path)


# get relevant paths
drawBotRoot = os.path.dirname(os.path.abspath(__file__))
distLocation = os.path.join(drawBotRoot, "dist")
appLocation = os.path.join(distLocation, "%s.app" % appName)
imgLocation = os.path.join(distLocation, "img")
existingDmgLocation = os.path.join(distLocation, "%s.dmg" % appName)
dmgLocation = os.path.join(distLocation, appName)


if "-A" not in sys.argv:
    # make sure the external tools have the correct permissions
    externalTools = ("ffmpeg", "gifsicle", "mkbitmap", "potrace")
    for externalTool in externalTools:
        externalToolPath = os.path.join(appLocation, "contents", "Resources", externalTool)
        os.chmod(externalToolPath, 0o775)


if runTests:
    appExecutable = os.path.join(drawBotRoot, "dist", appName + ".app", "Contents", "MacOS", appName)
    runAllTestsPath = os.path.join(drawBotRoot, "tests", "runAllTests.py")
    commands = [appExecutable, "--testScript=%s" % runAllTestsPath]
    print("Running DrawBot tests...")
    process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    stdout, stderr = process.communicate()
    okLine = stdout.splitlines()[-2].strip()
    if okLine.split()[-1] != "OK":
        print("*** TESTS FAILED ***")
        print("Run following command to see details:")
        print(" ".join(commands))
        sys.exit(1)
    else:
        print("Tests ok.")


if buildDMG or ftpHost is not None:
    assert "-A" not in sys.argv, "can't build .dmg when using py2app -A"

    if codeSignDeveloperName:
        # ================
        # = code singing =
        # ================
        print("---------------------")
        print("-   code signing    -")
        cmds = ["codesign", "--force", "--deep", "--sign", "Developer ID Application: %s" % codeSignDeveloperName, appLocation]
        popen = subprocess.Popen(cmds)
        popen.wait()
        print("- done code singing -")
        print("---------------------")

        print("------------------------------")
        print("- verifying with codesign... -")
        cmds = ["codesign", "--verify", "--verbose=4", appLocation]
        popen = subprocess.Popen(cmds)
        popen.wait()
        print("------------------------------")

        print("---------------------------")
        print("- verifying with spctl... -")
        cmds = ["spctl", "--verbose=4", "--raw", "--assess", "--type", "execute", appLocation]
        popen = subprocess.Popen(cmds)
        popen.wait()
        print("---------------------------")

    # ================
    # = creating dmg =
    # ================
    print("------------------------")
    print("-    building dmg...   -")
    if os.path.exists(existingDmgLocation):
        os.remove(existingDmgLocation)

    os.mkdir(imgLocation)
    os.rename(os.path.join(distLocation, "%s.app" % appName), os.path.join(imgLocation, "%s.app" % appName))
    tempDmgName = "%s.tmp.dmg" % appName

    os.system("hdiutil create -size 200m -srcfolder \"%s\" -volname %s -format UDZO \"%s\"" % (imgLocation, appName, os.path.join(distLocation, tempDmgName)))

    os.system("hdiutil convert -format UDZO -imagekey zlib-level=9 -o \"%s\" \"%s\"" % (dmgLocation, os.path.join(distLocation, tempDmgName)))

    os.remove(os.path.join(distLocation, tempDmgName))

    os.rename(os.path.join(imgLocation, "%s.app" % appName), os.path.join(distLocation, "%s.app" % appName))

    shutil.rmtree(imgLocation)

    print("- done building dmg... -")
    print("------------------------")

    if ftpHost and ftpPath and ftpLogin and ftpPassword:
        import ftplib
        print("-------------------------")
        print("-    uploading to ftp   -")
        session = ftplib.FTP(ftpHost, ftpLogin, ftpPassword)
        session.cwd(ftpPath)

        dmgFile = open(existingDmgLocation, 'rb')
        fileName = os.path.basename(existingDmgLocation)
        session.storbinary('STOR %s' % fileName, dmgFile)
        dmgFile.close()

        # store a version
        session.cwd("versionHistory")
        dmgFile = open(existingDmgLocation, 'rb')
        fileName, ext = os.path.splitext(fileName)
        fileName = fileName + "_" + timeStamp + ext
        session.storbinary('STOR %s' % fileName, dmgFile)
        dmgFile.close()

        print("- done uploading to ftp -")
        print("-------------------------")
        session.quit()
