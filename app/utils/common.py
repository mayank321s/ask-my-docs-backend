import fitz 
def convertStringToHyphen(s: str) -> str:
    """
    Converts a string to lowercase, replaces spaces with hyphens, and removes any other whitespace.
    """
    return s.lower().replace(" ", "-").replace("\t", "-").replace("\n", "-")

def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text
