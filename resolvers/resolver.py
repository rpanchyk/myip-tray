from abc import ABC, abstractmethod

from models.ip_info import IpInfo


class Resolver(ABC):

    def __init__(self, request_timeout):
        self.request_timeout = request_timeout

    @abstractmethod
    def get(self) -> IpInfo:
        pass
