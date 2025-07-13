from tortoise import Model, fields


class VectorChunk(Model):
    """Individual vector chunk belonging to a document."""

    id = fields.IntField(pk=True)
    documentId = fields.IntField(
        related_name="chunks",
        source_field="document_id",
        on_delete=fields.CASCADE
    )
    chunkId = fields.CharField(max_length=255, unique=True, source_field="chunk_id")
    metadata = fields.JSONField(null=True)
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "vector_chunks"

    def __str__(self):  # pragma: no cover
        return self.chunkId
