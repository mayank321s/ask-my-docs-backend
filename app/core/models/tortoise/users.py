from tortoise import Model, fields


class Users(Model):
    """Individual vector chunk belonging to a document."""

    id = fields.IntField(pk=True)
    firstName = fields.CharField(max_length=255, unique=True, source_field="first_name")
    lastName = fields.CharField(max_length=255, unique=True, source_field="last_name")
    roleCode = fields.CharField(max_length=255, unique=True, source_field="role_code")
    emailAddress = fields.CharField(max_length=255, unique=True, source_field="email_address")
    password = fields.CharField(max_length=255, unique=True, source_field="password")
    createdAt = fields.DatetimeField(auto_now_add=True, source_field="created_at")
    updatedAt = fields.DatetimeField(auto_now=True, source_field="updated_at")

    class Meta:
        table = "users"

    def __str__(self):  # pragma: no cover
        return self.emailAddress
