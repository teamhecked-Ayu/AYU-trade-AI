"""Create initial AYUAI persistent schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_table("decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("outcome", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_decisions_user_id", "decisions", ["user_id"])
    op.create_table("agent_performance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("agent", sa.String(length=128), nullable=False),
        sa.Column("predictions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_agent_performance_user_id", "agent_performance", ["user_id"])
    op.create_index("ix_agent_performance_agent", "agent_performance", ["agent"])


def downgrade() -> None:
    op.drop_index("ix_agent_performance_agent", table_name="agent_performance")
    op.drop_index("ix_agent_performance_user_id", table_name="agent_performance")
    op.drop_table("agent_performance")
    op.drop_index("ix_decisions_user_id", table_name="decisions")
    op.drop_table("decisions")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
