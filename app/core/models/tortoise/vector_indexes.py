from tortoise import Model, fields

from .projects import Project


class VectorIndex(Model):
    """Represents a vector store index (e.g., Pinecone collection) that groups namespaces."""

    id = fields.IntField(pk=True)
    index_name = fields.CharField(max_length=255, unique=True)
    project: fields.ForeignKeyRelation[Project] = fields.ForeignKeyField(
        "models.Project", related_name="indexes", on_delete=fields.CASCADE
    )
    dimension = fields.IntField()
    metric = fields.CharField(max_length=50, default="cosine")
    type = fields.CharField(max_length=50, default="dense")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "vector_indexes"

    def __str__(self) -> str:  # pragma: no cover
        return self.index_name
