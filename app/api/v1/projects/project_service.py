"""Service layer for Project operations (API v1)."""

from typing import List
from loguru import logger

from app.core.models.tortoise import Project


class ProjectService:
    """Provides CRUD operations for Projects for API v1."""

    @staticmethod
    async def create(name: str) -> Project:
        logger.info("[v1] Creating project: {}", name)
        return await Project.create(name=name)

    @staticmethod
    async def list_all() -> List[Project]:
        logger.info("[v1] Fetching all projects")
        return await Project.all().order_by("id")
