__author__ = 'bromix'

__all__ = ['run']

from .impl import Runner
from .impl import Context

__RUNNER__ = Runner()


def run(provider, context=None):
    if not context:
        context = Context()
        pass

    __RUNNER__.run(provider, context)
    pass
