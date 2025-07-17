from abc import ABC, abstractmethod


class Resolver(ABC):

    def __init__(self, request_timeout):
        self.request_timeout = request_timeout

    @abstractmethod
    def get(self):
        pass
