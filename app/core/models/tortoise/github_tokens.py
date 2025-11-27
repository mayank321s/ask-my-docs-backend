from tortoise import Model, fields


class GithubToken(Model):
    """Represents a collection of related indexes and documents."""

    id = fields.IntField(pk=True)
    userId = fields.IntField(
        source_field="user_id",
        on_delete=fields.CASCADE
    )
    token = fields.CharField(max_length=255)
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "github_token"

    def __str__(self) -> str:  # pragma: no cover
        return self.name
