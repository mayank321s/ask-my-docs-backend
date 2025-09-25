from tortoise import Model, fields


class GithubRepo(Model):

    id = fields.IntField(pk=True)
    userId = fields.IntField(
        source_field="user_id",
        on_delete=fields.CASCADE
    )
    repoName = fields.CharField(max_length=255)
    repoOwner = fields.CharField(max_length=255)
    repoUrl = fields.CharField(max_length=255)
    projectId = fields.IntField(
        source_field="project_id",
        on_delete=fields.CASCADE
    )
    categoryId = fields.IntField(
        source_field="category_id",
        on_delete=fields.CASCADE
    )
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "github_repo"

    def __str__(self) -> str:  # pragma: no cover
        return self.repoName
