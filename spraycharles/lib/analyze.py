import json
import numpy
from enum import Enum
from rich.table import Table
from typing import Tuple, Set

from spraycharles.lib.logger import console, logger
from spraycharles.lib.utils import SMBStatus, SprayResult, HookSvc, NotifyType, send_notification


class Analyzer:
    def __init__(self, resultsfile, notify, webhook, host, hit_count=0):
        self.resultsfile = resultsfile
        self.notify = notify
        self.webhook = webhook
        self.host = host
        self.hit_count = hit_count


    #
    # Run analysis over spray result file
    # Returns tuple of (hit_count, set of successful usernames)
    #
    def analyze(self) -> Tuple[int, Set[str]]:
        print()
        logger.debug(f"Opening results file: {self.resultsfile}")

        #
        # Output file isn't technically JSON compliant, but each line is a JSON object
        # So read each line and load into a list of JSON objects
        #
        with open(self.resultsfile, "r") as resultsfile:
            logger.info("Reading JSON spray result objects")
            responses = [json.loads(line) for line in resultsfile]
            
        #
        # Determine the type of service that was sprayed
        #
        match responses[0][SprayResult.MODULE]:
            case "Office365":
                return self.O365_analyze(responses)
            case "SMB":
                return self.smb_analyze(responses)
            case _:
                return self.http_analyze(responses)

    #
    # Analyzes O365 and Okta results
    #
    def O365_analyze(self, responses) -> Tuple[int, Set[str]]:
        results = []
        for line in responses:
            results.append(line.get("Result"))

        if "Success" in results:
            logger.info("Identified potentially successful logins!")
            print()

            success_table = Table(show_footer=False, highlight=True, title="Spray Hits", title_justify="left", title_style="bold reverse")

            success_table.add_column(SprayResult.USERNAME)
            success_table.add_column(SprayResult.PASSWORD)
            success_table.add_column(SprayResult.MESSAGE, justify="right")

            count = 0
            successful_users = set()
            for resp in responses:
                if resp.get(SprayResult.RESULT) == "Success":
                    count += 1
                    username = str(resp.get(SprayResult.USERNAME))
                    successful_users.add(username)
                    success_table.add_row(
                        username,
                        str(resp.get(SprayResult.PASSWORD)),
                        str(resp.get(SprayResult.MESSAGE))
                    )

            console.print(success_table)

            self._send_notification(count)

            return count, successful_users
        else:
            logger.info("No successful logins")
            print()
            return 0, set()


    #
    # Standard HTTP module analysis
    # Checks for outliers in both response length AND status code
    #
    def http_analyze(self, responses) -> Tuple[int, Set[str]]:
        # remove lines with timeouts
        responses = [line for line in responses if line.get(SprayResult.RESPONSE_CODE) != "TIMEOUT"]

        if not responses:
            logger.info("No responses to analyze (all timeouts)")
            print()
            return 0, set()

        response_lengths = []
        response_codes = []

        for line in responses:
            response_lengths.append(int(line.get(SprayResult.RESPONSE_LENGTH)))
            response_codes.append(int(line.get(SprayResult.RESPONSE_CODE)))

        logger.info("Analyzing response lengths and status codes")

        #
        # Find response length outliers (statistical)
        #
        length_elements = numpy.array(response_lengths)
        length_mean = numpy.mean(length_elements, axis=0)
        length_sd = numpy.std(length_elements, axis=0)

        length_outliers = set(
            x for x in length_elements
            if (x > length_mean + 2 * length_sd or x < length_mean - 2 * length_sd)
        )

        #
        # Find status code outliers (minority codes)
        # If a status code appears in < 10% of responses, it's an outlier
        #
        from collections import Counter
        code_counts = Counter(response_codes)
        total_responses = len(response_codes)
        code_outliers = set(
            code for code, count in code_counts.items()
            if count / total_responses < 0.1
        )

        logger.info("Checking for outliers")

        #
        # Collect all suspicious responses (length OR status code outlier)
        #
        successful_users = set()
        hits = []

        for resp in responses:
            resp_length = int(resp.get(SprayResult.RESPONSE_LENGTH))
            resp_code = int(resp.get(SprayResult.RESPONSE_CODE))

            is_length_outlier = resp_length in length_outliers
            is_code_outlier = resp_code in code_outliers

            if is_length_outlier or is_code_outlier:
                username = str(resp.get(SprayResult.USERNAME))
                successful_users.add(username)
                hits.append({
                    "username": username,
                    "password": str(resp.get(SprayResult.PASSWORD)),
                    "code": resp_code,
                    "length": resp_length,
                })

        if hits:
            logger.info("Identified potentially successful logins!")
            print()

            success_table = Table(show_footer=False, highlight=True, title="Spray Hits", title_justify="left", title_style="bold reverse")

            success_table.add_column(SprayResult.USERNAME)
            success_table.add_column(SprayResult.PASSWORD)
            success_table.add_column(SprayResult.RESPONSE_CODE, justify="right")
            success_table.add_column(SprayResult.RESPONSE_LENGTH, justify="right")

            for hit in hits:
                success_table.add_row(
                    hit["username"],
                    hit["password"],
                    str(hit["code"]),
                    str(hit["length"])
                )

            console.print(success_table)

            self._send_notification(len(hits))

            print()

            return len(hits), successful_users
        else:
            logger.info("No outliers found or not enough data to find statistical significance")
            print()
            return 0, set()


    #
    # Check for SMB successes against SMB status codes
    #
    def smb_analyze(self, responses) -> Tuple[int, Set[str]]:
        successes = []
        positive_statuses = [
            SMBStatus.STATUS_SUCCESS,
            SMBStatus.STATUS_ACCOUNT_DISABLED,
            SMBStatus.STATUS_PASSWORD_EXPIRED,
            SMBStatus.STATUS_PASSWORD_MUST_CHANGE,
        ]

        for result in responses:
            if SMBStatus(result.get(SprayResult.SMB_LOGIN)) in positive_statuses:
                successes.append(result)

        if len(successes) > 0:
            logger.info("Identified potentially successful logins!")
            print()

            success_table = Table(show_footer=False, highlight=True, title="Spray Hits", title_justify="left", title_style="bold reverse")
            success_table.add_column(SprayResult.USERNAME)
            success_table.add_column(SprayResult.PASSWORD)
            success_table.add_column(SprayResult.SMB_LOGIN)

            successful_users = set()
            for result in successes:
                username = str(result.get(SprayResult.USERNAME))
                successful_users.add(username)
                success_table.add_row(
                    username,
                    str(result.get(SprayResult.PASSWORD)),
                    str(result.get(SprayResult.SMB_LOGIN))
                )

            console.print(success_table)

            self._send_notification(len(successes))

            print()

            return len(successes), successful_users
        else:
            logger.info("No successful SMB logins")
            print()
            return 0, set()

    #
    # Send notification to specified webhook
    #
    def _send_notification(self, hit_total):

        #
        # We'll only send notifications if NEW successes are found
        #
        if hit_total > self.hit_count:
            if self.notify and self.webhook:
                print()
                logger.info(f"Sending notification to {self.notify.value} webhook")
                try:
                    send_notification(
                        self.webhook,
                        self.notify,
                        NotifyType.CREDS_FOUND,
                        self.host
                    )
                except Exception as e:
                    logger.warning(f"Failed to send notification: {e}")
