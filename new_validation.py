from __future__ import annotations

from html import unescape
from typing import TYPE_CHECKING, Optional, TypeAlias, Union
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from new_auth import authorize_service
from Scripts.community_downloader import get_post_channel_url
from Scripts.models import ChannelVaildationResult, CommunityPostVaildationResult, MainMenu, ProcessedRegularExpression, VideoVaildationResult
from Scripts.shared_imports import B, F, S, re
from Scripts.utils.errors import on_comments_disabled

if TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3 import YouTubeResource  # type: ignore

YOUTUBE_VIDEO_LINK_REGEX = re.compile(r"^\s*(?P<video_url>(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?))?(?P<video_id>[\w\-]{11})(?:(?(video_url)\S+|$))?\s*$")

_YTResource: TypeAlias = Optional["YouTubeResource"]


def _wrap_print(silent):
    return (lambda *args, **kwargs: None) if silent is True else print  # noqa: ARG005


def _get_channel_id_from_url(channel_link: str) -> Union[str, None]:
    # taken from https://stackoverflow.com/a/70154677/19114302
    resp = requests.get(channel_link)
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.content)
    channel_link_node = soup.select_one('meta[property="og:url"]')
    if channel_link_node is None:
        return None
    channel_url = urlparse(channel_link_node.attrs["content"])
    return channel_url.path[len("/channel/") :]


class YouTubeValidator:
    def __init__(self, *, service: _YTResource = None, silent: bool = False, basic_check: bool = False) -> None:
        self._slient = silent
        self._basic_check = basic_check
        self._service = service
        self._log = _wrap_print(self._slient)

    @property
    def service(self) -> YouTubeResource:
        if self._service is None:
            self._service = authorize_service()
        return self._service

    def video_id(self, user_input: str) -> VideoVaildationResult:
        user_input = user_input.strip()
        vidmatch = YOUTUBE_VIDEO_LINK_REGEX.match(user_input)
        if vidmatch is None:
            if self._basic_check is False:
                if "youtube.com" in user_input or "youtu.be" in user_input:
                    if "?v=" not in user_input:
                        self._log(f"\n{B.RED}{F.BLACK}Invalid Video link!{S.R} Did you accidentally enter a channel link (or something else) instead of a video link?")
                    else:
                        self._log(f"\n{B.RED}{F.BLACK}Invalid Video link!{S.R} Check that you copied it correctly. It should look something like \"youtube.com/watch?v=whatever-ID\" where 'whatever-ID' is 11 characters long.")
            else:
                self._log(f"\n{B.RED}{F.BLACK}Invalid Video link or ID!{S.R} Video IDs are 11 characters long.")
            return VideoVaildationResult(False)
        possibleVideoID = vidmatch.group("video_id")
        if self._basic_check is True:
            return VideoVaildationResult(len(possibleVideoID) == 11)

        response = (
            self.service.videos()
            .list(
                part="snippet,id,statistics",
                id=possibleVideoID,
                fields="items/id,items/snippet/channelId,items/snippet/channelTitle,items/statistics/commentCount,items/snippet/title",
            )
            .execute()
        )

        # Checks if video exists but is unavailable
        if not response["items"]:
            self._log(f"\n{B.RED}{F.WHITE} ERROR: {S.R} {F.RED}No info returned for ID: {S.R} {possibleVideoID} {F.LIGHTRED_EX} - Video may be unavailable or deleted.{S.R}")
            return VideoVaildationResult(False, None, None, None, None)

        item = response["items"][0]
        if possibleVideoID != item["id"]:
            self._log("Something very odd happened. YouTube returned a video ID, but it is not equal to what was queried!")
            return VideoVaildationResult(False, None, None, None, None)

        channelID = item["snippet"]["channelId"]
        channelTitle = item["snippet"]["channelTitle"]
        videoTitle = unescape(item["snippet"]["title"])
        # When comments are disabled, the commentCount is not included in the response, returning None
        commentCount = item["statistics"].get("commentCount")
        isCommentDisabled = commentCount is None

        return VideoVaildationResult(isVaild=True, possibleVideoID=possibleVideoID, videoTitle=videoTitle, commentCount=(-1 if isCommentDisabled else int(commentCount)), channelID=channelID, channelTitle=channelTitle, isCommentsDisabled=isCommentDisabled)

    def channel_id(self, user_input: str) -> ChannelVaildationResult:
        user_input = user_input.strip()
        isolatedChannelID = None
        # input channel id directly
        if re.match(r"UC[0-9A-Za-z_-]{21}[AQgw]", user_input):
            isolatedChannelID = user_input
        elif user_input.startswith("@"):
            # Check for handle validity: Only letters and numbers, periods, underscores, and hyphens, and between 3 and 30 characters
            if not re.match(r"^[a-zA-Z0-9._-]{3,30}$", user_input[1:]):
                self._log(f"\n{B.RED}{F.BLACK}Error:{S.R} You appear to have entered an invalid handle! It must be between 3 and 30 characters long and only contain letters, numbers, periods, underscores, and hyphens.")
                return ChannelVaildationResult(False)
            isolatedChannelID = _get_channel_id_from_url(f"https://youtube.com/{user_input}")
        else:
            parsed = urlparse(user_input)
            if parsed.hostname not in ("www.youtube.com", "youtube.com"):
                self._log(f"\n{B.RED}{F.BLACK}Invalid Channel link or ID!{S.R}")
                return ChannelVaildationResult(False)
            if parsed.path.startswith("/channel/"):
                # youtube.com/channel/<channel_id>
                isolatedChannelID = parsed.path[len("/channel/") :]
            elif parsed.path.startswith("/c/") or parsed.path.startswith("/user/"):
                # youtube.com/c/<customurl>
                # youtube.com/user/<username>
                isolatedChannelID = _get_channel_id_from_url(parsed.geturl())
            elif parsed.path.startswith("/@"):
                # youtube.com/@<handle>
                handle = parsed.path[1:]
                if not re.match(r"^[a-zA-Z0-9._-]{3,30}$", handle):
                    self._log(f"\n{B.RED}{F.BLACK}Error:{S.R} You appear to have entered an invalid handle! It must be between 3 and 30 characters long and only contain letters, numbers, periods, underscores, and hyphens.")
                    return ChannelVaildationResult(False)
                isolatedChannelID = _get_channel_id_from_url(f"https://youtube.com/@{handle}")
            else:
                # youtube.com/<custom legacy url>
                isolatedChannelID = _get_channel_id_from_url(parsed.geturl())
        if isolatedChannelID is None or len(isolatedChannelID) != 24 or isolatedChannelID[:2] != "UC":
            self._log(f"\n{B.RED}{F.BLACK}Invalid Channel link or ID!{S.R} Channel IDs are 24 characters long and begin with 'UC'.")
            return ChannelVaildationResult(False, None, None)
        response = self.service.channels().list(part="snippet", id=isolatedChannelID).execute()
        if response.get("items"):
            channelTitle = response["items"][0]["snippet"]["title"]
            return ChannelVaildationResult(True, isolatedChannelID, channelTitle)
        else:
            self._log(f"{F.LIGHTRED_EX}Error{S.R}: Unable to Get Channel Title. Please check the channel ID.")
            return ChannelVaildationResult(False, None, None)

    def community_post_id(self, post_url: str) -> CommunityPostVaildationResult:
        parsed = urlparse(post_url)
        if "/post/" in parsed.path:
            isolatedPostID = parsed.path[len("/post/") :]
        elif "/channel/" in parsed.path and "/community" in parsed.path and "lb=" in parsed.query:
            isolatedPostID = parse_qs(parsed.query)["lb"][0]
        else:
            isolatedPostID = post_url

        # Post IDs used to be shorter, but apparently now have a longer format
        if (len(isolatedPostID) == 26 or len(isolatedPostID) == 36) and isolatedPostID[:2] == "Ug":
            validatedPostUrl = "https://www.youtube.com/post/" + isolatedPostID
            postOwnerURL = get_post_channel_url(isolatedPostID)
            if postOwnerURL is None:
                # channel not found, invaild
                return CommunityPostVaildationResult(False)
            valid, postOwnerID, postOwnerUsername = self.channel_id(postOwnerURL)
            return CommunityPostVaildationResult(valid, isolatedPostID, validatedPostUrl, postOwnerID, postOwnerUsername)
        else:
            return CommunityPostVaildationResult(False, None, None, None, None)


def validate_video_id(
    user_input: str,
    /,
    *,
    silent: bool = False,
    basicCheck: bool = False,
    ytservice: Optional["YouTubeResource"] = None,
) -> Union[VideoVaildationResult, MainMenu]:
    vaildator = YouTubeValidator(service=ytservice, basic_check=basicCheck, silent=silent)
    resp = vaildator.video_id(user_input)
    if resp.isCommentsDisabled and resp.commentCount == -1 and not silent:
        return on_comments_disabled(resp.possibleVideoID, resp.videoTitle)  # type: ignore
    return resp


def validate_channel_id(
    inputted_channel: str,
    /,
    *,
    silent: bool = False,
    basicCheck: bool = False,
    ytservice: Optional["YouTubeResource"] = None,
) -> ChannelVaildationResult:
    vaildator = YouTubeValidator(service=ytservice, silent=silent, basic_check=basicCheck)
    return vaildator.channel_id(inputted_channel)


def validate_post_id(
    post_url: str,
    /,
    *,
    silent: bool = False,
    basicCheck: bool = False,
    ytservice: Optional["YouTubeResource"] = None,
) -> CommunityPostVaildationResult:
    vaildator = YouTubeValidator(silent=silent, basic_check=basicCheck, service=ytservice)
    return vaildator.community_post_id(post_url)


############################ Validate Regex Input #############################
# Checks if regex expression is valid, tries to add escapes if necessary
# From: https://stackoverflow.com/a/51782559/17312053
def validate_regex(regex_from_user: str) -> ProcessedRegularExpression:
    def _raw_check(r):
        try:
            re.compile(r)
            return True
        except re.error:
            return False

    for processedExpression in (regex_from_user, re.escape(regex_from_user)):
        is_vaild = _raw_check(processedExpression)
        if is_vaild:
            return ProcessedRegularExpression(is_vaild, processedExpression)
    else:
        return ProcessedRegularExpression(False, None)
