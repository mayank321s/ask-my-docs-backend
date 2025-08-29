from enum import Enum

from tortoise import Model, fields

from .vector_namespaces import VectorNamespace
from .projects import Project


class DocumentType(str, Enum):
    BRD = "BRD"
    TDD = "TDD"
    ClientDoc = "ClientDoc"
    Spec = "Spec"
    Sprint = "Sprint"
    Other = "Other"

    def __str__(self) -> str:  # pragma: no cover
        return str(self.value)

    @classmethod
    def _db_value(cls, value):  # pragma: no cover
        # Tortoise stores the enum value, not the instance
        return value.value


class Document(Model):
    """Represents a uploaded/source document that is split into chunks."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    type = fields.CharEnumField(enum_type=DocumentType, default=DocumentType.Other)
    namespaceId = fields.IntField(
        related_name="documents",
        source_field="namespace_id",
        on_delete=fields.CASCADE
    )
    team = fields.JSONField(null=True)
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "documents"

    def __str__(self) -> str:  # pragma: no cover
        return self.name
