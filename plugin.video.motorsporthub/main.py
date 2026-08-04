"""Motorsport Hub — Kodi add-on entry point."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "lib"))

from motorsporthub import run  # noqa: E402

if __name__ == "__main__":
    run()
