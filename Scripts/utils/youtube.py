#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import traceback
from html import unescape
from typing import Optional

import Scripts.auth as auth
import Scripts.validation as validation
from Scripts.shared_imports import B, F, S
from Scripts.utils.errors import (
    HttpError,
    print_error_title_fetch,
    print_exception_during_scan,
    print_http_error_during_scan,
)


################################### GET VIDEO TITLE ###############################################
def get_video_title(current, video_id):
    """
    Check if video title is in dictionary,
    if not get video title from video ID using YouTube API request,
    then return title.
    """
    if video_id in current.vidTitleDict:
        title = current.vidTitleDict[video_id]
    elif current.errorOccurred is False:
        try:
            results = auth.YOUTUBE.videos().list(part="snippet", id=video_id, fields="items/snippet/title", maxResults=1).execute()
        except HttpError as hx:
            traceback.print_exc()
            print_http_error_during_scan(hx)
            print_error_title_fetch()
            current.errorOccurred = True
            return "[Unavailable]"

        except Exception as ex:
            traceback.print_exc()
            print_exception_during_scan(ex)
            print_error_title_fetch()
            current.errorOccurred = True
            return "[Unavailable]"

        if results["items"]:
            title = unescape(results["items"][0]["snippet"]["title"])
            current.vidTitleDict[video_id] = title
        elif (len(video_id) == 26 or len(video_id) == 36) and video_id[0:2] == "Ug":
            title = "[Community Post - No Title]"
            current.vidTitleDict[video_id] = title
        else:
            title = "[Title Unavailable]"
            current.vidTitleDict[video_id] = title
    else:
        title = "[Title Unavailable]"

    return title


############################ Process Input Spammer IDs ###############################
def process_spammer_ids(rawString: str) -> tuple[bool, Optional[list[str]]]:
    """
    Takes single or list of spammer IDs, splits and sanitizes each, converts to list of channel IDs
    Returns list of channel IDs.
    """
    inputList = rawString.split(",")  # Split spammer IDs / Links by commas

    # Remove whitespace from each list item
    inputList = [item.strip() for item in inputList]
    inputList = list(filter(None, inputList))  # Remove empty strings from list
    IDList = inputList.copy()  # copy the list

    # Validate each ID in list
    for iditem in inputList:
        valid, iditem, _ = validation.validate_channel_id(iditem)
        if valid is False:
            print(f"{B.RED}{F.BLACK}Invalid{S.R} Channel ID or Link: {iditem}\n")
            return False, None

    return True, IDList
