import requests
from models.ip_info import IpInfo
from resolvers.resolver import Resolver


class IpApiResolver(Resolver):

    def get(self) -> IpInfo:
        try:
            print("Getting IpInfo via IpApiResolver ... ", end="")
            req = requests.get("http://ip-api.com/json/?fields=query,country,countryCode", timeout=self.request_timeout)

            if req.status_code != 200:
                raise Exception(f"Status: {req.status_code}")

            data = req.json()
            ip_info = IpInfo(data["query"], data["country"], data["countryCode"])
            print("Done:", ip_info)
            return ip_info
        except Exception as e:
            print("Error:", e)
            return IpInfo.unknown()
