from tortoise import Model, fields


class Project(Model):
    """Represents a collection of related indexes and documents."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "projects"

    def __str__(self) -> str:  # pragma: no cover
        return self.name
