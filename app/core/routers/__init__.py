from app.api.v1.projects.project_controller import router as projects_router
from app.api.v1.documents.documents_controller import router as documents_router
from app.api.v1.chat.chat_controller import router as chat_router
from app.utils.api.router import TypedAPIRouter

projects_router = TypedAPIRouter(router=projects_router, prefix="", tags=["projects"])
documents_router = TypedAPIRouter(router=documents_router, prefix="", tags=["documents"])
chat_router = TypedAPIRouter(router=chat_router, prefix="", tags=["chat"])