from pydantic import BaseModel

class PaginationResponseDto(BaseModel):
    currentPage: int
    itemsInCurrentPage: int
    itemsPerPage: int
    pageCount: int
    totalCount: int