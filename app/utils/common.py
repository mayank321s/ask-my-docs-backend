def convertStringToHyphen(s: str) -> str:
    """
    Converts a string to lowercase, replaces spaces with hyphens, and removes any other whitespace.
    """
    return s.lower().replace(" ", "-").replace("\t", "-").replace("\n", "-")
