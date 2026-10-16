from tortoise import Model, fields

class VectorNamespace(Model):
    """Logical partition inside a vector index."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    categoryName = fields.CharField(max_length=255, source_field="category_name")
    indexId : int = fields.IntField(source_field="index_id")
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "vector_namespaces"
        unique_together = ("name", "indexId")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.indexId}:{self.name}"
