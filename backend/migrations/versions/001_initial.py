# -*- coding: utf-8 -*-
"""
初始表结构迁移 — 创建所有数据库表
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建所有初始表"""
    # documents 表
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("original_title", sa.String(500), nullable=False, server_default=""),
        sa.Column("doc_type", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("source_path", sa.String(1000), nullable=False, server_default=""),
        sa.Column("source_url", sa.String(1000), nullable=False, server_default=""),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_file_reading", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("method", sa.String(50), nullable=False, server_default=""),
        sa.Column("model", sa.String(100), nullable=False, server_default=""),
        sa.Column("category", sa.String(50), nullable=False, server_default="其他"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("overall_evaluation", sa.Text(), nullable=False, server_default=""),
        sa.Column("title_suggestion", sa.String(500), nullable=False, server_default=""),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        sa.Column("search_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # sections 表
    op.create_table(
        "sections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.String(500), nullable=False, server_default=""),
        sa.Column("location_hint", sa.String(200), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("search_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # tags 表
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # document_tag 关联表
    op.create_table(
        "document_tag",
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id", "tag_id"),
    )

    # raw_documents 表
    op.create_table(
        "raw_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("doc_type", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("raw_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("pages_json", sa.JSON(), nullable=True),
        sa.Column("segments_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # search_chunks 表
    op.create_table(
        "search_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("chunk_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("doc_title", sa.String(500), nullable=False, server_default=""),
        sa.Column("doc_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("source", sa.String(1000), nullable=False, server_default=""),
        sa.Column("location", sa.String(200), nullable=False, server_default=""),
        sa.Column("section_title", sa.String(500), nullable=False, server_default=""),
        sa.Column("global_chunk_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_stored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # knowledge_profiles 表
    op.create_table(
        "knowledge_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("generated_by", sa.String(100), nullable=False, server_default="rule_based"),
        sa.Column("profile_json", sa.JSON(), nullable=True),
        sa.Column("total_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("knowledge_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("main_focus", sa.String(200), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # background_tasks 表
    op.create_table(
        "background_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("message", sa.String(500), nullable=False, server_default=""),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # system_configs 表
    op.create_table(
        "system_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(200), nullable=False, unique=True),
        sa.Column("value_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("value_type", sa.String(20), nullable=False, server_default="string"),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """回滚所有表"""
    op.drop_table("system_configs")
    op.drop_table("background_tasks")
    op.drop_table("knowledge_profiles")
    op.drop_table("search_chunks")
    op.drop_table("raw_documents")
    op.drop_table("document_tag")
    op.drop_table("tags")
    op.drop_table("sections")
    op.drop_table("documents")
