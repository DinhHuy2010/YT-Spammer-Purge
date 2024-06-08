from Scripts.shared_imports import F, S

############################### User Choice #################################


def choice(message: str = "", bypass: bool = False) -> bool | None:
    """
    User inputs Y/N for choice, returns True or False
    Takes in message to display
    """
    if bypass is True:
        return True

    # While loop until valid input
    valid = False
    while valid is False:
        response = input(
            "\n" + message + f" ({F.LIGHTCYAN_EX}y{S.R}/{F.LIGHTRED_EX}n{S.R}): "
        ).strip()
        if response == "Y" or response == "y":
            return True
        elif response == "N" or response == "n":
            return False
        elif response == "X" or response == "x":
            return None
        else:
            print("\nInvalid Input. Enter Y or N  --  Or enter X to return to main menu.")
