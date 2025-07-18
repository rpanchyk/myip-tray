class IpInfo:
    def __init__(self, ip_address, county_name, country_code):
        self.ip_address = ip_address
        self.county_name = county_name
        self.country_code = country_code

    @staticmethod
    def unknown():
        return IpInfo(None, None, None)

    def is_unknown(self) -> bool:
        return self.ip_address is None or self.country_code is None

    def __repr__(self):
        return f"IpInfo(ip_address={self.ip_address}, county_name={self.county_name}, country_code={self.country_code})"
