"""Stalker VOD plugin entry point"""
from __future__ import absolute_import, division, unicode_literals

if __name__ == '__main__':
    from sys import argv
    from lib.addon import run
    run(argv)
