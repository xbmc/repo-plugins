# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
if __name__ == '__main__':
    import sys
    from tmdbhelper.lib.items.router import Router
    Router(int(sys.argv[1]), sys.argv[2][1:]).run()
