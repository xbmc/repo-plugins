# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Addon entry point"""

from __future__ import absolute_import, division, unicode_literals

if __name__ == '__main__':
    from sys import argv
    from addon import run
    run(argv)
