class IpInfo:
    def __init__(self, ip_address, county_name, country_code, error):
        self.ip_address = ip_address
        self.country_name = county_name
        self.country_code = country_code
        self.error = error

    @staticmethod
    def unknown(error: Exception):
        return IpInfo(None, None, None, error)

    def is_unknown(self) -> bool:
        return (self.error is not None
                or self.ip_address is None
                or self.country_name is None
                or self.country_code is None)

    def __repr__(self):
        return (f"IpInfo("
                f"ip_address={self.ip_address}, "
                f"country_name={self.country_name}, "
                f"country_code={self.country_code}, "
                f"error={self.error}"
                f")")
