import regex as re


######################### Check List Against String #########################
def check_list_against_string(
    listInput: list[str], stringInput: str, caseSensitive: bool = False
) -> bool:
    """Checks if any items in a list are a substring of a string."""
    if caseSensitive is False:
        stringInput = stringInput.lower()
        listInput = [item.lower() for item in listInput]
    return bool(any(x in stringInput for x in listInput))


################### Process Comma-Separated String to List ####################
def string_to_list(rawString: str, lower: bool = False) -> list[str]:
    """Take in string, split by commas, remove whitespace and empty items, and return list."""

    if lower is True:
        rawString = rawString.lower()

    # Remove whitespace
    newList = [n.strip() for n in rawString.split(",")]

    # Remove empty strings from list
    return list(filter(None, newList))


########################## Expand Number Ranges #############################
def expand_ranges(stringInput: str) -> str:
    return re.sub(
        r"(\d+)-(\d+)",
        lambda match: ",".join(str(i) for i in range(int(match.group(1)), int(match.group(2)) + 1)),
        stringInput,
    )


######################### Convert string to set of characters#########################
def make_char_set(
    stringInput: str,
    stripLettersNumbers: bool = False,
    stripKeyboardSpecialChars: bool = False,
    stripPunctuation: bool = False
):
    # Optional lists of characters to strip from string
    translateDict = {}
    charsToStrip = " "
    if stripLettersNumbers is True:
        numbersLettersChars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        charsToStrip += numbersLettersChars
    if stripKeyboardSpecialChars is True:
        keyboardSpecialChars = r"!@#$%^&*()_+-=[]\{\}|;':,./<>?`~"
        charsToStrip += keyboardSpecialChars
    if stripPunctuation is True:
        punctuationChars = "!?\".,;:'-/()"
        charsToStrip += punctuationChars

    # Adds characters to dictionary to use with translate to remove these characters
    for c in charsToStrip:
        translateDict[ord(c)] = None
    translateDict[ord("\ufe0f")] = None  # Strips invisible varation selector for emojis

    # Removes charsToStrip from string
    stringInput = stringInput.translate(translateDict)
    listedInput = list(stringInput)

    return set(filter(None, listedInput))
