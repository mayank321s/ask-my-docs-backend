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



    project: fields.ForeignKeyRelation[Project] = fields.ForeignKeyField(
        "models.Project", related_name="documents", on_delete=fields.CASCADE
    )
    namespace: fields.ForeignKeyRelation[VectorNamespace] = fields.ForeignKeyField(
        "models.VectorNamespace", related_name="documents", on_delete=fields.CASCADE
    )
    file_path = fields.TextField(null=True)
    team = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "documents"

    def __str__(self) -> str:  # pragma: no cover
        return self.name
