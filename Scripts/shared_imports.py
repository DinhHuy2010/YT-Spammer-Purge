import os
import sys
import traceback

import colorama
import colorama.ansi
import regex as re
from colorama import init as colorama_init


# Workaround for ruff type check
class AnsiStyle(colorama.ansi.AnsiStyle):
    R = 0


class AnsiFore(colorama.ansi.AnsiFore):
    R = 39


class AnsiBack(colorama.ansi.AnsiBack):
    R = 49


S, F, B = AnsiStyle(), AnsiFore(), AnsiBack()

# Global Hardcoded Constants
VERSION = "2.18.0-Beta3-DinhHuy2010"
CONFIG_VERSION = 33
RESOURCES_FOLDER_NAME = "SpamPurge_Resources"

__all__ = ["os", "sys", "re", "traceback", "F", "B", "S", "colorama_init", "RESOURCES_FOLDER_NAME"]
