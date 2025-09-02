from app.api.v1.projects.project_controller import router as projects_router
from app.api.v1.documents.documents_controller import router as documents_router
from app.api.v1.chat.chat_controller import router as chat_router
from app.api.v1.github.github_controller import router as github_router
from app.api.v2.projects.project_controller import router as projects_router_v2
from app.api.v2.documents.documents_controller import router as documents_router_v2
from app.api.v2.chat.chat_controller import router as chat_router_v2
from app.api.v2.github.github_controller import router as github_router_v2
from app.api.v2.auth.auth_controller import router as auth_router_v2
from app.utils.api.router import TypedAPIRouter
from app.utils.jwt import JWTHandler
from fastapi import Depends

projects_router = TypedAPIRouter(router=projects_router, prefix="", tags=["projects"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
documents_router = TypedAPIRouter(router=documents_router, prefix="", tags=["documents"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
chat_router = TypedAPIRouter(router=chat_router, prefix="", tags=["chat"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
github_router = TypedAPIRouter(router=github_router, prefix="", tags=["github"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
projects_routerV2 = TypedAPIRouter(router=projects_router_v2, prefix="/v2", tags=["projects"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
documents_routerV2 = TypedAPIRouter(router=documents_router_v2, prefix="/v2", tags=["documents"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
chat_routerV2 = TypedAPIRouter(router=chat_router_v2, prefix="/v2", tags=["chat"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
github_routerV2 = TypedAPIRouter(router=github_router_v2, prefix="/v2", tags=["github"], dependencies=[Depends(JWTHandler.decodeAccessToken)])
auth_routerV2 = TypedAPIRouter(router=auth_router_v2, prefix="/v2", tags=["auth"])
