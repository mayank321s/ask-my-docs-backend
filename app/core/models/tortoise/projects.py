from tortoise import Model, fields


class Project(Model):
    """Represents a collection of related indexes and documents."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "projects"

    def __str__(self) -> str:  # pragma: no cover
        return self.name
