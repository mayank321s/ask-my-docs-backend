from tortoise import Model, fields

from .documents import Document


class VectorChunk(Model):
    """Individual vector chunk belonging to a document."""

    id = fields.IntField(pk=True)
    document: fields.ForeignKeyRelation[Document] = fields.ForeignKeyField(
        "models.Document", related_name="chunks", on_delete=fields.CASCADE
    )
    chunk_id = fields.CharField(max_length=255, unique=True)
    metadata = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "vector_chunks"

    def __str__(self):  # pragma: no cover
        return self.chunk_id
