"""add idempotent chat features and conversation state"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "phase39_chat_features_01"
down_revision = "phase0_member_schema_01"
branch_labels = None
depends_on = None
U = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)

def upgrade() -> None:
    op.create_table("chat_conversation_preferences",
        sa.Column("id", U, primary_key=True), sa.Column("conversation_id", U, nullable=False), sa.Column("user_id", U, nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("muted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("last_read_at", TS), sa.Column("updated_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("conversation_id", "user_id", name="uq_chat_conversation_pref"))
    op.create_table("chat_message_features",
        sa.Column("message_id", U, primary_key=True), sa.Column("conversation_id", U, nullable=False), sa.Column("sender_user_id", U, nullable=False),
        sa.Column("client_message_id", U, nullable=False), sa.Column("reply_to_message_id", U),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_user_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["reply_to_message_id"], ["chat_messages.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("conversation_id", "sender_user_id", "client_message_id", name="uq_chat_message_client_id"))
    op.create_table("chat_message_reactions", sa.Column("id", U, primary_key=True), sa.Column("message_id", U, nullable=False), sa.Column("user_id", U, nullable=False), sa.Column("emoji", sa.String(32), nullable=False), sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("message_id", "user_id", "emoji", name="uq_chat_message_reaction"))
    op.create_table("chat_message_pins", sa.Column("message_id", U, primary_key=True), sa.Column("pinned_by_user_id", U, nullable=False), sa.Column("created_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["pinned_by_user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("message_id", name="uq_chat_message_pin"))
    op.create_table("chat_message_deliveries", sa.Column("id", U, primary_key=True), sa.Column("message_id", U, nullable=False), sa.Column("user_id", U, nullable=False), sa.Column("delivered_at", TS, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("read_at", TS), sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("message_id", "user_id", name="uq_chat_message_delivery"))

def downgrade() -> None:
    for table in ("chat_message_deliveries", "chat_message_pins", "chat_message_reactions", "chat_message_features", "chat_conversation_preferences"):
        op.drop_table(table)
