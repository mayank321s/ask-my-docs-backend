from tortoise import Model, fields
from .projects import Project


class VectorIndex(Model):
    """Represents a vector store index (e.g., Pinecone collection) that groups namespaces."""

    id = fields.IntField(pk=True)
    indexName = fields.CharField(max_length=255, unique=True, source_field="index_name")
    projectId = fields.IntField(
        source_field="project_id",
        on_delete=fields.CASCADE
    )
    dimension = fields.IntField(default=1024)
    metric = fields.CharField(max_length=50, default="cosine")
    type = fields.CharField(max_length=50, default="dense")
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "vector_indexes"  # Explicit snake_case table name

    def __str__(self) -> str:  # pragma: no cover
        return self.indexName  # Use the Python attribute name