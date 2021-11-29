import AppKit
import io


def PIL2NSImage(pilImage):
    buffer = io.BytesIO()
    pilImage.save(buffer, pilImage.format)
    data = buffer.getvalue()
    data = AppKit.NSData.dataWithBytes_length_(data, len(data))
    nsImage = AppKit.NSImage.alloc().initWithData_(data)
    return nsImage
