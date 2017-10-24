from distutils.core import setup
from distutils import sysconfig
import py2app
import os
import sys
import subprocess
import shutil
import tempfile
import datetime
from plistlib import readPlist, writePlist

import vanilla
import defconAppKit
# import robofab
import fontTools
import pygments

from drawBot.drawBotSettings import __version__, appName

rawTimeStamp = datetime.datetime.today()
timeStamp = rawTimeStamp.strftime("%y%m%d%H%M")

def getValueFromSysArgv(key, default=None):
    if key in sys.argv:
        try:
            i = sys.argv.index(key)
            value = sys.argv[i+1]
            sys.argv.remove(key)
            sys.argv.remove(value)
            return value
        except:
            pass
    return default

codeSignDeveloperName = getValueFromSysArgv("--codesign")

ftpHost = getValueFromSysArgv("--ftphost")
ftpPath = getValueFromSysArgv("--ftppath")
ftpLogin = getValueFromSysArgv("--ftplogin")
ftpPassword = getValueFromSysArgv("--ftppassword")

osxMinVersion = "10.9.0"

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
    CFBundleIconFile="DrawBot.icns",
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

for fileName in os.listdir("Resources/Images"):
    baseName, extension = os.path.splitext(fileName)
    if extension.lower() in [".png", ".icns"]:
        fullPath = os.path.join("Resources/Images", fileName)
        dataFiles.append(fullPath)

# build
setup(
    data_files=dataFiles,
    app=[dict(script="DrawBot.py", plist=plist)],
    options=dict(py2app=dict(
                    packages=[
                        'vanilla',
                        'defcon',
                        'defconAppKit',
                        # 'robofab',
                        'fontParts',
                        'mutatorMath',
                        'woffTools',
                        'compositor',
                        'feaTools2',
                        'ufo2svg',
                        'booleanOperations',
                        #'pyclipper',
                        'pygments',
                        'jedi',
                        'fontTools',
                        # 'xml'
                        ],
                    includes=[
                        # 'csv',
                        # 'this'
                        ],
                    excludes=[
                        "numpy",
                        "scipy",
                        "mathplitlib",
                        "PIL",
                        "pygame",
                        "wx"
                        ]
                    )
                )
            )

# fix the icon
path = os.path.join(os.path.dirname(__file__), "dist", "DrawBot.app", "Contents", "Info.plist")
appPlist = readPlist(path)
appPlist["CFBundleIconFile"] = "DrawBot.icns"
writePlist(appPlist, path)

if "-A" not in sys.argv:
    # get relevant paths
    distLocation = os.path.join(os.getcwd(), "dist")
    appLocation = os.path.join(distLocation, "%s.app" % appName)
    imgLocation = os.path.join(distLocation, "img")
    existingDmgLocation = os.path.join(distLocation, "%s.dmg" % appName)
    dmgLocation = os.path.join(distLocation, appName)

    # copy external tools into the resources folder (gifsicle)
    gifsiclePathSource = os.path.join(os.getcwd(), "drawBot", "context", "tools", "gifsicle")
    gifsiclePathDest = os.path.join(appLocation, "contents", "Resources", "gifsicle")
    print "copy", gifsiclePathSource, gifsiclePathDest
    shutil.copyfile(gifsiclePathSource, gifsiclePathDest)
    os.chmod(gifsiclePathDest, 0775)

    mkbitmapPathSource = os.path.join(os.getcwd(), "drawBot", "context", "tools", "mkbitmap")
    mkbitmapPathDest = os.path.join(appLocation, "contents", "Resources", "mkbitmap")
    print "copy", mkbitmapPathSource, mkbitmapPathDest
    shutil.copyfile(mkbitmapPathSource, mkbitmapPathDest)
    os.chmod(mkbitmapPathDest, 0775)

    potracePathSource = os.path.join(os.getcwd(), "drawBot", "context", "tools", "potrace")
    potracePathDest = os.path.join(appLocation, "contents", "Resources", "potrace")
    print "copy", potracePathSource, potracePathDest
    shutil.copyfile(potracePathSource, potracePathDest)
    os.chmod(potracePathDest, 0775)


    if codeSignDeveloperName:
        # ================
        # = code singing =
        # ================
        print "---------------------"
        print "-   code signing    -"
        cmds = ["codesign", "--force", "--deep", "--sign", "Developer ID Application: %s" % codeSignDeveloperName, appLocation]
        popen = subprocess.Popen(cmds)
        popen.wait()
        print "- done code singing -"
        print "---------------------"

        print "------------------------------"
        print "- verifying with codesign... -"
        cmds = ["codesign", "--verify", "--verbose=4", appLocation]
        popen = subprocess.Popen(cmds)
        popen.wait()
        print "------------------------------"

        print "---------------------------"
        print "- verifying with spctl... -"
        cmds = ["spctl", "--verbose=4", "--raw", "--assess", "--type", "execute", appLocation]
        popen = subprocess.Popen(cmds)
        popen.wait()
        print "---------------------------"

    # ================
    # = creating dmg =
    # ================
    print "------------------------"
    print "-    building dmg...   -"
    if os.path.exists(existingDmgLocation):
        os.remove(existingDmgLocation)

    os.mkdir(imgLocation)
    os.rename(os.path.join(distLocation, "%s.app" % appName), os.path.join(imgLocation, "%s.app" % appName))
    tempDmgName = "%s.tmp.dmg" % appName

    os.system("hdiutil create -srcfolder \"%s\" -volname %s -format UDZO \"%s\"" % (imgLocation, appName, os.path.join(distLocation, tempDmgName)))

    os.system("hdiutil convert -format UDZO -imagekey zlib-level=9 -o \"%s\" \"%s\"" % (dmgLocation, os.path.join(distLocation, tempDmgName)))

    os.remove(os.path.join(distLocation, tempDmgName))

    os.rename(os.path.join(imgLocation, "%s.app" % appName), os.path.join(distLocation, "%s.app" % appName))

    shutil.rmtree(imgLocation)

    print "- done building dmg... -"
    print "------------------------"

    if ftpHost and ftpPath and ftpLogin and ftpPassword:
        import ftplib
        print "-------------------------"
        print "-    uploading to ftp   -"
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
        fileName = fileName + timeStamp + ext
        session.storbinary('STOR %s' % fileName, dmgFile)
        dmgFile.close()

        print "- done uploading to ftp -"
        print "-------------------------"
        session.quit()
