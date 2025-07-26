import requests

from models.ip_info import IpInfo
from resolvers.resolver import Resolver


class MyIpResolver(Resolver):

    def get(self) -> IpInfo:
        try:
            req = requests.get("https://api.myip.com", timeout=self.request_timeout)

            if req.status_code != 200:
                raise Exception(f"Status: {req.status_code}")

            data = req.json()
            return IpInfo(data["ip"], data["country"], data["cc"], None)
        except Exception as e:
            return IpInfo.unknown(e)
