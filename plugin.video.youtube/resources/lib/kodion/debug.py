__author__ = 'bromix'


def debug_here(host='localhost'):
    import pydevd
    pydevd.settrace(host, stdoutToServer=True, stderrToServer=True)
    pass
