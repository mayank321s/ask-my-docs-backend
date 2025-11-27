from tortoise import Model, fields


class Chat(Model):
    """Represents a collection of related indexes and documents."""

    id = fields.IntField(pk=True)
    projectId = fields.IntField(
        related_name="projects",
        source_field="project_id",
        on_delete=fields.CASCADE
    )
    categoryId = fields.IntField(
        related_name="vector_namespaces",
        source_field="category_id",
        on_delete=fields.CASCADE,
        null=True
    )
    userId = fields.IntField(
        related_name="projects",
        source_field="user_id",
        on_delete=fields.CASCADE
    )
    sessionId = fields.CharField(max_length=255)
    chatHistory = fields.JSONField()
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "chats"

    def __str__(self) -> str:  # pragma: no cover
        return self.name
