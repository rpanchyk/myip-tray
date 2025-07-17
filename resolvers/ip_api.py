import requests
from models.ip_info import IpInfo
from resolvers.resolver import Resolver


class IpApiResolver(Resolver):

    def get(self):
        try:
            print("Getting IpInfo via IpApiResolver started")
            req = requests.get("http://ip-api.com/json/", timeout=self.request_timeout)

            if req.status_code != 200:
                raise Exception(f"Status: {req.status_code}")

            data = req.json()
            ip_info = IpInfo(data["query"], data["countryCode"])
            print("Getting IpInfo via IpApiResolver finished:", ip_info)
            return ip_info
        except Exception as e:
            print("Getting IpInfo via IpApiResolver failed:", e)
            return False
