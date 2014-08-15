from distutils.core import setup
from distutils import sysconfig
import py2app
import os
import sys
import subprocess
import shutil
import tempfile
from plistlib import readPlist, writePlist

import vanilla
import defconAppKit
import robofab
import fontTools
import pygments

from drawBotSettings import __version__, appName

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

plist = dict(

	CFBundleDocumentTypes = [
	dict(
		CFBundleTypeExtensions = ["py"],
		CFBundleTypeName = "Python Source File",
		CFBundleTypeRole = "Editor",
        CFBundleTypeIconFile = "pythonIcon.icns",
		NSDocumentClass = "DrawBotDocument",
	    ),

		],
	CFBundleIdentifier = "com.drawbot",
	LSMinimumSystemVersion = "10.6.0",
	CFBundleShortVersionString = __version__,
	CFBundleVersion = __version__,
	CFBundleIconFile = "DrawBot.icns",
	NSHumanReadableCopyright = "Copyright by Just van Rossum and Frederik Berlaen.",
    CFBundleURLTypes = [
            dict(
                CFBundleURLName = "com.drawbot",
                CFBundleURLSchemes = [appName.lower()])
        ],
	)


dataFiles = [
        "Resources/English.lproj",
        #os.path.dirname(vanilla.__file__),
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
    options = dict(py2app=dict(
                    packages=[
                        'vanilla',
                        'defcon',
                        'defconAppKit',
                        'robofab',
                        'pygments',
                        'jedi',
                        'fontTools',
                        'xml'
                        ],
                    includes=[
                        'csv',
                        'this'
                        ],
                    )
                )
            )

# fix the icon
path = os.path.join(os.path.dirname(__file__), "dist", "DrawBot.app", "Contents", "Info.plist")
appPlist = readPlist(path)
appPlist["CFBundleIconFile"] = "DrawBot.icns"
writePlist(appPlist, path)

if "-A" not in sys.argv and codeSignDeveloperName:
    # get relevant paths
    distLocation = os.path.join(os.getcwd(), "dist")
    appLocation = os.path.join(distLocation, "%s.app" % appName)
    imgLocation = os.path.join(distLocation,  "img")
    existingDmgLocation = os.path.join(distLocation,  "%s.dmg" % appName)
    dmgLocation = os.path.join(distLocation,  appName)

    # copy external tools into the resources folder (gifsicle)
    resourcesPath = os.path.join(appLocation, "contents", "Resources", "tools")
    toolsSourcePath = os.path.join(os.getcwd(), "drawBot", "context", "tools")
    print "copy", toolsSourcePath, resourcesPath
    shutil.copytree(toolsSourcePath, resourcesPath)

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
    os.rename(os.path.join(distLocation, "%s.app" %appName), os.path.join(imgLocation, "%s.app" %appName))
    tempDmgName = "%s.tmp.dmg" %appName

    os.system("hdiutil create -srcfolder \"%s\" -volname %s -format UDZO \"%s\"" %(imgLocation, appName, os.path.join(distLocation, tempDmgName)))

    os.system("hdiutil convert -format UDZO -imagekey zlib-level=9 -o \"%s\" \"%s\"" %(dmgLocation, os.path.join(distLocation, tempDmgName)))

    os.remove(os.path.join(distLocation, tempDmgName))

    os.rename(os.path.join(imgLocation, "%s.app" %appName), os.path.join(distLocation, "%s.app" %appName))

    shutil.rmtree(imgLocation)

    print "- done building dmg... -"
    print "------------------------"

    if ftpHost and ftpPath and ftpLogin and ftpPassword:
        import ftplib
        print "-------------------------"
        print "-    uploading to ftp   -"
        session = ftplib.FTP(ftpHost, ftpLogin, ftpPassword)
        session.cwd(ftpPath)

        dmgFile = open(existingDmgLocation,'rb')
        fileName = os.path.basename(existingDmgLocation)

        session.storbinary('STOR %s' % fileName, dmgFile)
        dmgFile.close()
        print "- done uploading to ftp -"
        print "-------------------------"
        session.quit()




