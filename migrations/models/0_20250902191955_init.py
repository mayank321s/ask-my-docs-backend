from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "documents" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "type" VARCHAR(9) NOT NULL DEFAULT 'Other',
    "namespace_id" INT NOT NULL,
    "team" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "documents"."type" IS 'BRD: BRD\nTDD: TDD\nClientDoc: ClientDoc\nSpec: Spec\nSprint: Sprint\nOther: Other';
COMMENT ON TABLE "documents" IS 'Represents a uploaded/source document that is split into chunks.';
CREATE TABLE IF NOT EXISTS "projects" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "user_id" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "projects" IS 'Represents a collection of related indexes and documents.';
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "first_name" VARCHAR(255) NOT NULL UNIQUE,
    "last_name" VARCHAR(255) NOT NULL UNIQUE,
    "role_code" VARCHAR(255) NOT NULL UNIQUE,
    "email_address" VARCHAR(255) NOT NULL UNIQUE,
    "password" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "vector_chunks" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "document_id" INT NOT NULL,
    "chunk_id" VARCHAR(255) NOT NULL UNIQUE,
    "metadata" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "vector_chunks" IS 'Individual vector chunk belonging to a document.';
CREATE TABLE IF NOT EXISTS "vector_indexes" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "index_name" VARCHAR(255) NOT NULL UNIQUE,
    "project_id" INT NOT NULL,
    "dimension" INT NOT NULL DEFAULT 1024,
    "metric" VARCHAR(50) NOT NULL DEFAULT 'cosine',
    "type" VARCHAR(50) NOT NULL DEFAULT 'dense',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "vector_indexes" IS 'Represents a vector store index (e.g., Pinecone collection) that groups namespaces.';
CREATE TABLE IF NOT EXISTS "vector_namespaces" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "category_name" VARCHAR(255) NOT NULL,
    "index_id" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "uid_vector_name_name_1bdcf9" UNIQUE ("name", "index_id")
);
COMMENT ON TABLE "vector_namespaces" IS 'Logical partition inside a vector index.';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
