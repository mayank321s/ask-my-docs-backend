from tortoise import Model, fields


class GithubBranch(Model):

    id = fields.IntField(pk=True)
    userId = fields.IntField(
        source_field="user_id",
        on_delete=fields.CASCADE
    )
    githubRepoId = fields.IntField(
        source_field="github_repo_id",
        on_delete=fields.CASCADE
    )
    branchName = fields.CharField(max_length=255)
    branchRepoUrl = fields.CharField(max_length=255)
    status = fields.CharField(max_length=50, default="uploading")
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "github_branch"

    def __str__(self) -> str:  # pragma: no cover
        return self.branchName
