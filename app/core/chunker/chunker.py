from langchain.text_splitter import RecursiveCharacterTextSplitter
from uuid import uuid4

# def chunkText(text, metadata, file_name):
#     splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
#     chunks = splitter.split_text(text)
#     return [
#         {
#             "_id": f"{file_name}_{i}_{uuid4().hex[:6]}",
#             "chunk_text": chunk,
#             **metadata
#         }
#         for i, chunk in enumerate(chunks)
#     ]

def chunkText(text: str, metadata: dict, file_name: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    chunks = splitter.split_text(text)

    return [
        {
            "_id": str(uuid4()), 
            "chunk_text": chunk,
            **metadata
        }
        for chunk in chunks
    ]