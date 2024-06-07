import os
import sys

# for get_terminal_size()
if os.name == "nt":
    # For Windows
    _get_terminal_size = os.get_terminal_size
else:
    # For Unix-based systems
    from shutil import get_terminal_size as _get_terminal_size

########################## Get Console Window Width #############################
# To determine how many characters to print in a line
def get_terminal_size() -> int:
    return _get_terminal_size().columns

def clear_terminal() -> None:
    try:
        is_term = sys.stdout.isatty()
    except Exception:
        is_term = False
    if is_term:  # if in a terminal
        if sys.platform.startswith("win"):
            # For windows, use cls
            os.system("cls")
        else:
            # For MacOS / Linux, this should clear the screen
            sys.stdout.write("\033[2J\033[1;1H")
    else:
        # Do nothing if not a terminal
        return
    # Not 100% sure if there are any cases where sys.stdout.isatty can raise an exception
