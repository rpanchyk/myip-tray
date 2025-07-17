class IpInfo:
    def __init__(self, ip_address, country_code):
        self.ip_address = ip_address
        self.country_code = country_code

    def __repr__(self):
        return f"IpInfo(ip_address={self.ip_address}, country_code={self.country_code})"
