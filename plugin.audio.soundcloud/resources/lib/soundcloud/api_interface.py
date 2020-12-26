from abc import ABCMeta, abstractmethod


class ApiInterface(metaclass=ABCMeta):
    @abstractmethod
    def search(self, query, kind): pass

    @abstractmethod
    def charts(self, filters): pass

    @abstractmethod
    def call(self, url): pass

    @abstractmethod
    def discover(self, selection): pass

    @abstractmethod
    def resolve_id(self, id): pass

    @abstractmethod
    def resolve_url(self, url): pass

    @abstractmethod
    def resolve_media_url(self, url): pass
