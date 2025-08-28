from app.api.v1.projects.project_controller import router as projects_router
from app.api.v1.documents.documents_controller import router as documents_router
from app.api.v1.chat.chat_controller import router as chat_router
from app.api.v1.github.github_controller import router as github_router
from app.api.v2.projects.project_controller import router as projects_router_v2
from app.api.v2.documents.documents_controller import router as documents_router_v2
from app.api.v2.chat.chat_controller import router as chat_router_v2
from app.api.v2.github.github_controller import router as github_router_v2
from app.utils.api.router import TypedAPIRouter

projects_router = TypedAPIRouter(router=projects_router, prefix="", tags=["projects"])
documents_router = TypedAPIRouter(router=documents_router, prefix="", tags=["documents"])
chat_router = TypedAPIRouter(router=chat_router, prefix="", tags=["chat"])
github_router = TypedAPIRouter(router=github_router, prefix="", tags=["github"])
projects_routerV2 = TypedAPIRouter(router=projects_router_v2, prefix="/v2", tags=["projects"])
documents_routerV2 = TypedAPIRouter(router=documents_router_v2, prefix="/v2", tags=["documents"])
chat_routerV2 = TypedAPIRouter(router=chat_router_v2, prefix="/v2", tags=["chat"])
github_routerV2 = TypedAPIRouter(router=github_router_v2, prefix="/v2", tags=["github"])