from tortoise import Model, fields


class GithubPullRequest(Model):

    id = fields.IntField(pk=True)
    userId = fields.IntField(
        source_field="user_id",
        on_delete=fields.CASCADE
    )
    githubRepoId = fields.IntField(
        source_field="github_repo_id",
        on_delete=fields.CASCADE
    )
    prNumber = fields.IntField(
        source_field="pr_number",
        on_delete=fields.CASCADE
    )
    prUrl = fields.CharField(max_length=255)
    prName = fields.CharField(max_length=255)
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "github_pull_request"

    def __str__(self) -> str:  # pragma: no cover
        return self.prNumber
