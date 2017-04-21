#!/usr/bin/env python

import argparse
import io
import os
import shutil
import tempfile
import urllib2

import PIL.Image
import PIL.PngImagePlugin


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('filename')
    args = parser.parse_args()

    download = urllib2.urlopen(args.url)
    buffered = io.BytesIO(download.read())
    PIL.Image.open(buffered).verify()
    # The image must be re-opened after verification.
    buffered.seek(0)
    image = PIL.Image.open(buffered)
    saved = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as saved:
            image.save(saved, PIL.PngImagePlugin.PngImageFile.format)

        # Atomically move to the desired location. (This is only atomic if the
        # temp directory is on the same filesystem).
        shutil.move(saved.name, args.filename)
        saved = None
    finally:
        if saved is not None:
            try:
                os.remove(saved.name)
            except OSError:
                pass


if __name__ == "__main__":
    main()
