"""p0: 会话结束请求时间 + 消息全文检索索引

Revision ID: p0_conv_end_ft
Revises: 7a88f4834311
Create Date: 2026-08-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p0_conv_end_ft"
down_revision: Union[str, None] = "7a88f4834311"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 会话增加"结束请求时间"（24h 超时自动生效，PRD 6.5.6 规则 5）
    op.add_column("conversations", sa.Column("end_requested_at", sa.DateTime(), nullable=True, comment="结束请求时间"))

    # 2. 消息全文检索索引（MySQL ngram 中文分词，PRD F-403）
    op.execute(
        "ALTER TABLE messages ADD FULLTEXT INDEX ft_ix_messages_content (content, translated_text) WITH PARSER ngram"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE messages DROP INDEX ft_ix_messages_content")
    op.drop_column("conversations", "end_requested_at")
