import fitz
from io import BytesIO
from docx import Document as _DocxDocument

def convertStringToHyphen(s: str) -> str:
    return s.lower().replace(" ", "-").replace("\t", "-").replace("\n", "-")

def extractTextFromPdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extractTextFromDocx(uploaded_file):
    file_bytes = uploaded_file.file.read()
    buffer = BytesIO(file_bytes)
    doc = _DocxDocument(buffer)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text