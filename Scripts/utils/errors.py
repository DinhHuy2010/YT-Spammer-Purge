import sys
import traceback
from json import JSONDecodeError
from typing import NoReturn

from googleapiclient.errors import HttpError

from Scripts.constants import B, F, S


def print_exception_reason(reason: str) -> None:
    print(f"    Reason: {reason}")

    if reason == "processingFailure":
        print(
            f"\n {F.LIGHTRED_EX}[!!] Processing Error{S.R} - Sometimes this error fixes itself. \
            Try just running the program again. !!"
        )
        print("This issue is often on YouTube's side, so if it keeps happening try again later.")
        print(
            "(This also occurs if you try deleting comments on someone else's video, \
            which is not possible.)"
        )
    elif reason == "commentsDisabled":
        print(
            f"\n{F.LIGHTRED_EX}[!] Error:{S.R} Comments are disabled on this video. This error can \
            also occur if scanning a live stream."
        )
    elif reason == "quotaExceeded":
        print(
            f"\n{F.LIGHTRED_EX}Error:{S.R} You have exceeded the YouTube API quota. \
            To do more scanning you must wait until the quota resets."
        )
        print(
            " > There is a daily limit of 10,000 units/day, which works out to around \
            reporting 10,000 comments/day."
        )
        print(" > You can check your quota by searching 'quota' in the Google Cloud console.")
        print(
            f"{F.YELLOW}Solutions: Either wait until tomorrow, or create additional projects \
            in the cloud console.{S.R}"
        )
        print(
            f"  > Read more about the quota limits for this app here: \
            {F.YELLOW}TJoe.io/api-limit-info{S.R}"
        )


def print_http_error_during_scan(hx: HttpError) -> None:
    print("------------------------------------------------")
    print(f"{B.RED}{F.WHITE} ERROR! {S.R}  Error Message: " + str(hx))
    if hx.status_code:
        print("Status Code: " + str(hx.status_code))
        # If error reason is available, print it
        if hx.error_details[0]["reason"]:  # type: ignore
            reason = hx.error_details[0]["reason"]  # type: ignore
            print_exception_reason(reason)


def print_exception_during_scan(ex: Exception) -> None:
    print("------------------------------------------------")
    print(f"{B.RED}{F.WHITE} ERROR! {S.R}  Error Message: {ex}")


def print_break_finished(scanMode: str) -> None:
    print("------------------------------------------------")
    print(
        f"\n{F.LIGHTRED_EX}[!] Fatal Error Occurred During Scan! {F.BLACK}{B.LIGHTRED_EX} Read the \
        important info below! {S.R}"
    )
    print(
        f"\nProgram must skip the rest of the scan. {F.LIGHTGREEN_EX}Comments already scanned can \
        still be used to create a log file (if you choose){S.R}"
    )
    print(
        f"  > You won't be able to delete/hide any comments like usual, but you can \
        {F.LIGHTMAGENTA_EX} exclude users before saving the log file{S.R}"
    )
    print(
        f"  > Then, you can {F.LIGHTGREEN_EX}delete the comments later{S.R} using the {F.YELLOW} \
        mode that removes comments using a pre-existing list{S.R}"
    )
    if scanMode == "entireChannel":
        print(
            f"{F.RED}NOTE: {S.R} Because of the scanning mode (entire channel) the log will be \
            missing the video IDs and video names."
        )
    input("\n Press Enter to Continue...")

def print_error_title_fetch() -> None:
    print("--------------------------------------------------------------------------------------------------------------------------")
    print(
        f"\n{F.BLACK}{B.RED} ERROR OCCURRED {S.R} While Fetching Video Title... \
        {F.BLACK}{B.LIGHTRED_EX} READ THE INFO BELOW {S.R}"
    )
    print(
        f"Program will {F.LIGHTGREEN_EX}attempt to continue{S.R}, but the {F.YELLOW}video title \
        may not be available{S.R} in the log file."
    )
    print(
        f"  > You won't be able to delete/hide any comments like usual, but you can \
        {F.LIGHTMAGENTA_EX}exclude users before saving the log file{S.R}"
    )
    print(
        f"  > Then, you can {F.LIGHTGREEN_EX}delete the comments later{S.R} \
        using the {F.YELLOW}mode that removes comments using a pre-existing log file{S.R}"
    )
    input("\n Press Enter to Continue...")

# authorization stuff

def no_client_secrets() -> NoReturn:
    print(f"\n         ----- {F.WHITE}{B.RED}[!] Error:{S.R} client_secrets.json file not found -----")
    print(
        f" ----- Did you create a {F.YELLOW}Google Cloud Platform Project{S.R} to access the API? ----- "  # noqa: E501
    )
    print(f"  > For instructions on how to get an API key, visit: {F.YELLOW}TJoe.io/api-setup{S.R}")
    print("\n  > (Non-shortened Link: https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Instructions:-Obtaining-an-API-Key)")
    input("\nPress Enter to Exit...")
    sys.exit()

def fail_client_secrets_loading(jx: JSONDecodeError) -> NoReturn:
    print(f"{F.WHITE}{B.RED} [!!!] Error: {S.R}" + str(jx))
    print(
        f"\nDid you make the client_secrets.json file yourself by {F.LIGHTRED_EX}copying and pasting into it{S.R}, instead of {F.LIGHTGREEN_EX}downloading it{S.R}?"  # noqa: E501
    )
    print(
        f"You need to {F.YELLOW}download the json file directly from the Google Cloud dashboard{S.R} as shown in the instructions."
    )
    print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
    input("Press Enter to Exit...")
    sys.exit()

def fail_to_authorize(exc: Exception) -> bool:
    if "invalid_grant" in str(exc):
        print(f"{F.YELLOW}[!] Invalid token{S.R} - Requires Re-Authentication")
        return True
    else:
        print("\n")
        traceback.print_exc()  # Prints traceback
        print("----------------")
        print(f"{F.RED}[!!!] Error: {S.R}" + str(exc))
        print("If you think this is a bug, you may report it on this project's GitHub page: https://github.com/ThioJoe/YT-Spammer-Purge/issues")
        input(
            f"\nError Code A-1: {F.RED}Something went wrong during authentication.{S.R} {F.YELLOW} \
            Try deleting the token.pickle file.{S.R} \nPress Enter to Exit..."
        )
        return False
