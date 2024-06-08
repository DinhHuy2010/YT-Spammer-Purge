from dataclasses import dataclass
from typing import NamedTuple, Optional, TypeGuard, Union


# Declare Classes
@dataclass
class ScanInstance:
    matchedCommentsDict: dict  # Comments flagged by the filter
    duplicateCommentsDict: dict  # Comments flagged as duplicates
    repostedCommentsDict: dict  # Comments stolen from other users
    otherCommentsByMatchedAuthorsDict: dict  # Comments not matched, but are by a matched author
    scannedThingsList: list  # List of posts or videos that were scanned
    spamThreadsDict: dict  # Comments flagged as parent of spam threads
    allScannedCommentsDict: dict  # All comments scanned for this instance
    vidIdDict: dict  # Contains the video ID on which each comment is found
    vidTitleDict: dict  # Contains the titles of each video ID
    matchSamplesDict: dict  # Contains sample info for every flagged comment of all types
    authorMatchCountDict: dict  # The number of flagged comments per author
    scannedRepliesCount: int  # The current number of replies scanned so far
    scannedCommentsCount: int  # The current number of comments scanned so far
    logTime: str  # The time at which the scan was started
    logFileName: Optional[str]  # Contains a string of the current date/time to be used as a log file name or anything else
    errorOccurred: bool  # True if an error occurred during the scan

@dataclass
class MiscDataStore:
    resources: dict
    spamLists: dict
    totalCommentCount: int
    channelOwnerID: str
    channelOwnerName: str

class MainMenu:
    pass

RETURN_TO_MAIN_MENU = MainMenu()

def is_main_menu_state(obj: Union[object, type]) -> TypeGuard[MainMenu]:
    if obj is RETURN_TO_MAIN_MENU:
        return True
    if isinstance(obj, type):
        return issubclass(obj, MainMenu)
    return isinstance(obj, MainMenu)

class CurrentUser(NamedTuple):
    id: str
    name: str
    configMatch: Optional[bool] = None
