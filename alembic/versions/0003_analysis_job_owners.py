"""Track ownership for submitted analysis jobs."""

from alembic import op
import sqlalchemy as sa

revision = "0003_analysis_job_owners"
down_revision = "0002_provider_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_analysis_jobs_user_id", "analysis_jobs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_analysis_jobs_user_id", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
