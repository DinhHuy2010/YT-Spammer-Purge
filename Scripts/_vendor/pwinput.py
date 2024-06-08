"""PWInput
By Al Sweigart al@inventwithpython.com

A cross-platform Python module that displays **** for password input. Formerly called stdiomask.

Modfied by DinhHuy2010 (https://github.com/DinhHuy2010).
NOTICE: remove python 2 support
"""

__version__ = "1.0.3"

import getpass as gp
import sys


def _getch() -> str:
    if sys.platform == "win32":
        from msvcrt import getch

        return getch().decode()
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def pwinput(prompt: str = "Password: ", mask: str = "*") -> str:
    if not isinstance(prompt, str):
        raise TypeError("prompt argument must be a str, not %s" % (type(prompt).__name__))
    if not isinstance(mask, str):
        raise TypeError("mask argument must be a zero- or one-character str, not %s" % (type(prompt).__name__))
    if len(mask) > 1:
        raise ValueError("mask argument must be a zero- or one-character str")

    if mask == "" or sys.stdin is not sys.__stdin__:
        # Fall back on getpass if a mask is not needed.
        return gp.getpass(prompt)

    enteredPassword: list[str] = []
    sys.stdout.write(prompt)
    sys.stdout.flush()

    while True:
        key = ord(_getch())
        if key == 13:  # Enter key pressed.
            sys.stdout.write("\n")
            return "".join(enteredPassword)
        elif key in (8, 127):  # Backspace/Del key erases previous output.
            if len(enteredPassword) > 0:
                # Erases previous character.
                sys.stdout.write("\b \b")  # \b doesn't erase the character, it just moves the cursor back.
                sys.stdout.flush()
                enteredPassword = enteredPassword[:-1]
        elif 0 <= key <= 31:
            if key == 3:
                raise KeyboardInterrupt
            # Do nothing for unprintable characters.
            # TODO: Handle Esc, F1-F12, arrow keys, home, end, insert, del, pgup, pgdn
            if key == 26:
                raise EOFError
        else:
            # Key is part of the password; display the mask character.
            char = chr(key)
            sys.stdout.write(mask)
            sys.stdout.flush()
            enteredPassword.append(char)

def _test() -> None:
    pwd = pwinput()
    print("data:", pwd)

if __name__ == "__main__":
    _test()
