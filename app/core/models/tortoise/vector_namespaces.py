from tortoise import Model, fields

from .vector_indexes import VectorIndex


class VectorNamespace(Model):
    """Logical partition inside a vector index."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    index: fields.ForeignKeyRelation[VectorIndex] = fields.ForeignKeyField(
        "models.VectorIndex", related_name="namespaces", on_delete=fields.CASCADE
    )
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "vector_namespaces"
        unique_together = ("name", "index")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.index.index_name}:{self.name}"
