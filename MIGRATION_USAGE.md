# Database Migrations with Aerich

This document explains how to use Aerich for database migrations in this Python backend project.

## Setup

Aerich has been configured for this project with the following setup:

### 1. Configuration Files

- **pyproject.toml**: Contains Aerich configuration pointing to the Tortoise ORM settings
- **app/config/aerich.py**: Contains the Tortoise ORM configuration for Aerich

### 2. Migration Directory Structure

```
migrations/
├── models/
│   ├── 0_20250902191955_init.py          # Initial migration (all tables)
│   └── 1_20250902192030_add_description_to_project.py  # Sample migration
└── ...
```

## Common Aerich Commands

### Initialize Aerich (Already Done)
```bash
aerich init-db
```
This creates the initial migration based on your current models.

### Create a New Migration
```bash
aerich migrate --name "migration_name"
```
This generates a new migration file based on model changes.

### Apply Migrations
```bash
aerich upgrade
```
This applies all pending migrations to the database.

### Rollback Migrations
```bash
aerich downgrade
```
This rolls back the last applied migration.

### Check Migration Status
```bash
aerich history
```
This shows the migration history.

## Example: Adding a Field to a Model

### Step 1: Modify the Model
Add a new field to your Tortoise model:

```python
# app/core/models/tortoise/projects.py
class Project(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField(null=True, blank=True)  # New field
    userId = fields.IntField(...)
    # ... other fields
```

### Step 2: Generate Migration
```bash
aerich migrate --name "add_description_to_project"
```

### Step 3: Apply Migration
```bash
aerich upgrade
```

## Migration File Structure

Each migration file contains:

```python
from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "projects" ADD "description" TEXT;
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "projects" DROP COLUMN "description";
    """
```

## Best Practices

1. **Always create migrations for model changes**: Never modify the database schema manually
2. **Use descriptive migration names**: Make it clear what the migration does
3. **Test migrations**: Always test both upgrade and downgrade operations
4. **Review generated SQL**: Check the generated migration files before applying
5. **Backup before major migrations**: Always backup your database before applying migrations in production

## Current Models

The project currently includes these models:
- **Project**: Represents a collection of related indexes and documents (includes userId field)
- **User**: User management
- **Document**: Uploaded/source documents
- **VectorIndex**: Vector store indexes
- **VectorNamespace**: Logical partitions inside vector indexes
- **VectorChunk**: Individual vector chunks belonging to documents

## Notes

- The `userId` field already exists in the Project model as requested
- The sample migration demonstrates adding a `description` field to the Project table
- All migrations are tracked in the `aerich` table in the database
- The configuration supports both PostgreSQL (production) and SQLite (testing)