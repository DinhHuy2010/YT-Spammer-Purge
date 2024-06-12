from __future__ import annotations

from html import unescape
from typing import TYPE_CHECKING, NamedTuple, Optional, Union, cast
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from new_auth import authorize_service
from Scripts.models import RETURN_TO_MAIN_MENU, MainMenu
from Scripts.shared_imports import B, F, S, re
from Scripts.utils.stringstuff import check_list_against_string

if TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3 import YouTubeResource  # type: ignore


class VideoVaildationResult(NamedTuple):
    isVaild: bool
    possibleVideoID: Optional[str] = None
    videoTitle: Optional[str] = None
    commentCount: Optional[int] = None
    channelID: Optional[str] = None
    channelTitle: Optional[str] = None


class ChannelVaildationResult(NamedTuple):
    isVaild: bool
    channelID: Optional[str] = None
    channelTitle: Optional[str] = None


YOUTUBE_VIDEO_LINK_REGEX = re.compile(r"^\s*(?P<video_url>(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?))?(?P<video_id>[\w\-]{11})(?:(?(video_url)\S+|$))?\s*$")


def _get_youtube_service(service: Optional["YouTubeResource"]):
    if service is None:
        return authorize_service()
    return service


def _wrap_print(silent):
    return (lambda *args, **kwargs: None) if silent is True else print  # noqa: ARG005


def _get_more_video_info(possibleVideoID, printer, pass_exception, *, ytservice=None) -> Union[VideoVaildationResult, MainMenu]:
    YOUTUBE = _get_youtube_service(ytservice)
    try:
        response = (
            YOUTUBE.videos()
            .list(
                part="snippet,id,statistics",
                id=possibleVideoID,
                fields="items/id,items/snippet/channelId,items/snippet/channelTitle,items/statistics/commentCount,items/snippet/title",
            )
            .execute()
        )

        # Checks if video exists but is unavailable
        if len(response["items"]) == 0:
            printer(f"\n{B.RED}{F.WHITE} ERROR: {S.R} {F.RED}No info returned for ID: {S.R} {possibleVideoID} {F.LIGHTRED_EX} - Video may be unavailable or deleted.{S.R}")
            return VideoVaildationResult(False, None, None, None, None)

        item = response["items"][0]

        if possibleVideoID != item["id"]:
            printer("Something very odd happened. YouTube returned a video ID, but it is not equal to what was queried!")
            return VideoVaildationResult(False, None, None, None, None)

        channelID = item["snippet"]["channelId"]
        channelTitle = item["snippet"]["channelTitle"]
        videoTitle = unescape(item["snippet"]["title"])
        # When comments are disabled, the commentCount is not included in the response, requires catching KeyError
        commentCount = item["statistics"].get("commentCount")
        if commentCount is None:
            if pass_exception is True:
                # If the video has comments disabled, the commentCount is not included in the response, but the video is still valid
                return VideoVaildationResult(True, possibleVideoID, videoTitle, 0, channelID, channelTitle)
            print("--------------------------------------")
            print(f"\n{B.RED}{F.WHITE} ERROR: {S.R} {F.RED}Unable to get comment count for video: {S.R} {possibleVideoID}  |  {videoTitle}")
            print(f"\n{F.YELLOW}Are comments disabled on this video?{S.R} If not, please report the bug and include the error info above.")
            print(f"                    Bug Report Link: {F.YELLOW}TJoe.io/bug-report{S.R}")
            input("\nPress Enter to return to the main menu...")
            return RETURN_TO_MAIN_MENU

        return VideoVaildationResult(True, possibleVideoID, videoTitle, int(commentCount), channelID, channelTitle)
    except Exception:
        printer(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
        return VideoVaildationResult(False, None, None, None, None)


def validate_video_id(
    user_input: str,
    /,
    *,
    silent: bool = False,
    pass_exception: bool = False,
    basicCheck: bool = False,
    ytservice: Optional["YouTubeResource"] = None,
) -> Union[VideoVaildationResult, MainMenu]:
    printer = _wrap_print(silent=silent)
    user_input = user_input.strip()
    match = YOUTUBE_VIDEO_LINK_REGEX.match(user_input)
    if match is None:
        if basicCheck is False:
            if ("youtube.com" in user_input or "youtu.be" in user_input) and "?v=" not in user_input:
                printer(f"\n{B.RED}{F.BLACK}Invalid Video link!{S.R} Did you accidentally enter a channel link (or something else) instead of a video link?")
            elif "youtube.com" in user_input or "youtu.be" in user_input:
                printer(f"\n{B.RED}{F.BLACK}Invalid Video link!{S.R} Check that you copied it correctly. It should look something like \"youtube.com/watch?v=whatever-ID\" where 'whatever-ID' is 11 characters long.")
            else:
                printer(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
        return VideoVaildationResult(False)
    else:
        possibleVideoID = match.group("video_id")
        if basicCheck is True:
            return VideoVaildationResult(len(possibleVideoID) == 11)
        else:
            return _get_more_video_info(possibleVideoID, printer, pass_exception, ytservice=ytservice)


def _get_channel_id_from_url(channel_link: str) -> Union[str, None]:
    # modfied from https://stackoverflow.com/a/70154677/19114302
    resp = requests.get(channel_link)
    if resp.content != 200:
        return None
    soup = BeautifulSoup(resp.content)
    channel_link_node = soup.select_one('meta[property="og:url"]')
    if channel_link_node is None:
        return None
    channel_url = urlparse(channel_link_node.attrs["content"])
    print(f"{channel_url=}")
    return channel_url.path[len("/channel/") :]

def _get_channel_id(user_input: str) -> Union[str, None]:
    notChannelList = ["?v", "v=", "/embed/", "/vi/", "?feature=", "/v/", "/e/"]
    channelPrefix = "/channel/"
    urlparsed = urlparse(user_input)
    if urlparsed.path[-1] == "/":
        urlparsed = urlparsed._replace(path=urlparsed.path[:-1])

    # Channel ID regex expression from: https://webapps.stackexchange.com/a/101153
    if re.match(r"UC[0-9A-Za-z_-]{21}[AQgw]", user_input):
        return user_input
    # Get id from channel link
    elif channelPrefix in urlparsed.path:
        return user_input[len(channelPrefix) :]
    elif urlparsed.path.startswith("/c/") or urlparsed.path.startswith("/user/"):
        return _get_channel_id_from_url(urlparsed.geturl())

    # Handle legacy style custom URL (no /c/ for custom URL)
    elif not check_list_against_string(notChannelList, user_input, caseSensitive=True) and urlparsed.hostname is not None and urlparsed.hostname.lower() in ("youtube.com", "www.youtube.com"):
        # First check if actually video ID (video ID regex expression from: https://webapps.stackexchange.com/a/101153)
        customURL = urlparsed.path[1:]
        if re.match(r"[0-9A-Za-z_-]{10}[048AEIMQUYcgkosw]", customURL):
            print(f"{F.LIGHTRED_EX}Invalid Channel ID / Link!{S.R} Did you enter a video ID / link by mistake?")
            return None
        return _get_channel_id_from_url(urlparsed.geturl())

    # Check if new "handle" identifier is used
    elif user_input.lower().startswith("@"):
        # Check for handle validity: Only letters and numbers, periods, underscores, and hyphens, and between 3 and 30 characters
        if not re.match(r"^[a-zA-Z0-9._-]{3,30}$", user_input[1:]):
            print(f"\n{B.RED}{F.BLACK}Error:{S.R} You appear to have entered an invalid handle! It must be between 3 and 30 characters long and only contain letters, numbers, periods, underscores, and hyphens.")
            return None
        # Does a search for the handle and gets the channel ID from first response
        # return _get_channel_id_from_search(user_input)
        return _get_channel_id_from_url(f"https://www.youtube.com/{user_input}")
    else:
        print(f"\n{B.RED}{F.BLACK}Error:{S.R} Invalid Channel link or ID!")
        return None


def validate_channel_id(inputted_channel: str, /, *, ytservice: Optional["YouTubeResource"] = None) -> ChannelVaildationResult:
    YOUTUBE = _get_youtube_service(ytservice)
    inputted_channel = inputted_channel.strip()

    # Check if link is actually a video link / ID
    isVideo = cast(VideoVaildationResult, validate_video_id(inputted_channel, silent=True, basicCheck=True))
    if isVideo.isVaild:
        print(f"\n{F.BLACK}{B.LIGHTRED_EX} Invalid Channel ID / Link! {S.R} Looks like you entered a Video ID / Link by mistake.")
        return ChannelVaildationResult(False, None, None)

    isolatedChannelID = _get_channel_id(inputted_channel)

    if isolatedChannelID is None or len(isolatedChannelID) != 24 or isolatedChannelID[:2] != "UC":
        print(f"\n{B.RED}{F.BLACK}Invalid Channel link or ID!{S.R} Channel IDs are 24 characters long and begin with 'UC'.")
        return ChannelVaildationResult(False, None, None)
    response = YOUTUBE.channels().list(part="snippet", id=isolatedChannelID).execute()
    if response.get("items"):
        channelTitle = response["items"][0]["snippet"]["title"]
        return ChannelVaildationResult(True, isolatedChannelID, channelTitle)
    else:
        print(f"{F.LIGHTRED_EX}Error{S.R}: Unable to Get Channel Title. Please check the channel ID.")
        return ChannelVaildationResult(False, None, None)


def _test() -> None:
    video_test_input = "https://www.youtube.com/watch?v=pCYHkmU9kqw"
    result = validate_video_id(video_test_input)
    print(result)


if __name__ == "__main__":
    _test()
