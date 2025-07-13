from app.api.v1.projects.project_controller import router as projects_router
from app.api.v1.documents.documents_controller import router as documents_router
from app.utils.api.router import TypedAPIRouter

projects_router = TypedAPIRouter(router=projects_router, prefix="", tags=["projects"])
documents_router = TypedAPIRouter(router=documents_router, prefix="", tags=["documents"])