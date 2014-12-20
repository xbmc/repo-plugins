__author__ = 'bromix'


class AbstractProviderRunner(object):
    def run(self, provider, context=None):
        raise NotImplementedError()

    pass