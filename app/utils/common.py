import fitz
import math
from io import BytesIO
from docx import Document as _DocxDocument

from app.core.models.pydantic.pagination import PaginationResponseDto

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

def getPaginationResponse(
    total_rows_count: int,
    limit: int,
    page: int,
    total_records: int,
) -> PaginationResponseDto:
    return PaginationResponseDto(
        currentPage=page,
        itemsInCurrentPage=total_records,
        itemsPerPage=limit,
        pageCount=math.ceil(total_rows_count / limit),
        totalCount=total_rows_count,
    )