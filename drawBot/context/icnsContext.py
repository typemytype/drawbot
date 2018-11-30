import Quartz
import os
import shutil
import tempfile

from drawBot.misc import executeExternalProcess, DrawBotError
from drawBot.context.imageContext import ImageContext


class ICNSContext(ImageContext):

    fileExtensions = ["icns"]

    allowedPageSizes = [16, 32, 128, 256, 512, 1024]

    def _writeDataToFile(self, data, path, options):
        # create a iconset folder
        iconsetPath = tempfile.mkdtemp(suffix=".iconset")
        try:
            # get the complete pdf
            pdfDocument = Quartz.PDFDocument.alloc().initWithData_(data)
            pageCount = pdfDocument.pageCount()
            # set the image resolution
            options["imageResolution"] = 72
            # make a copy and alter the resolution
            options_2x = dict(options)
            options_2x["imageResolution"] = 144
            # start loop over all pages
            for index in range(pageCount):
                # get the pdf page
                page = pdfDocument.pageAtIndex_(index)
                # get the pdf page, this acts also as pdf document...
                pageData = page.dataRepresentation()
                # extract the size of the page
                _, (w, h) = page.boundsForBox_(Quartz.kPDFDisplayBoxArtBox)
                w = int(round(w))
                h = int(round(h))
                # dont allow any other size, the command iconutil will not work otherwise
                if w not in self.allowedPageSizes or w != h:
                    raise DrawBotError("The .icns can not be build with the size '%sx%s'. Must be either: %s" % (w, h, ", ".join(["%sx%s" % (i, i) for i in self.allowedPageSizes])))
                # generate a 72 dpi png in the iconset path
                pngPath = os.path.join(iconsetPath, "icon_%sx%s.png" % (w, h))
                super(ICNSContext, self)._writeDataToFile(pageData, pngPath, options)
                # generate a 144 dpi png in the iconset path
                pngPath_2x = os.path.join(iconsetPath, "icon_%sx%s@2x.png" % (w, h))
                super(ICNSContext, self)._writeDataToFile(pageData, pngPath_2x, options_2x)
            # collect all iconutil commands
            cmds = [
                "iconutil",
                "--convert",
                "icns",
                "--output",
                path,
                iconsetPath,
            ]
            # execute the commands
            stdout, stderr = executeExternalProcess(cmds)
        finally:
            # always remove the iconset
            shutil.rmtree(iconsetPath)
