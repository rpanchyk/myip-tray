import requests
from models.ip_info import IpInfo
from resolvers.resolver import Resolver


class MyIpResolver(Resolver):

    def get(self):
        try:
            print("Getting IpInfo via MyIpResolver started")
            req = requests.get("https://api.myip.com", timeout=self.request_timeout)

            if req.status_code != 200:
                raise Exception(f"Status: {req.status_code}")

            data = req.json()
            ip_info = IpInfo(data["ip"], data["cc"])
            print("Getting IpInfo via MyIpResolver finished:", ip_info)
            return ip_info
        except Exception as e:
            print("Getting IpInfo via MyIpResolver failed:", e)
            return False
