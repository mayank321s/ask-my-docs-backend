from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "projects" ADD "user_id" INTEGER;
        ALTER TABLE "projects" ADD CONSTRAINT "fk_projects_user_id" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE;
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "projects" DROP CONSTRAINT "fk_projects_user_id";
        ALTER TABLE "projects" DROP COLUMN "user_id";
    """
