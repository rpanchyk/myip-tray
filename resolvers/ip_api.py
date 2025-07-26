import requests

from models.ip_info import IpInfo
from resolvers.resolver import Resolver


class IpApiResolver(Resolver):

    def get(self) -> IpInfo:
        try:
            req = requests.get("http://ip-api.com/json/?fields=query,country,countryCode", timeout=self.request_timeout)

            if req.status_code != 200:
                raise Exception(f"Status: {req.status_code}")

            data = req.json()
            return IpInfo(data["query"], data["country"], data["countryCode"], None)
        except Exception as e:
            return IpInfo.unknown(e)
