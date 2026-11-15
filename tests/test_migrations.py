from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_fresh_database_migrations_create_provider_credentials(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config("alembic.ini")

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert "users" in inspector.get_table_names()
        assert "decisions" in inspector.get_table_names()
        assert "agent_performance" in inspector.get_table_names()
        assert "provider_credentials" in inspector.get_table_names()

        columns = {column["name"] for column in inspector.get_columns("provider_credentials")}
        assert columns == {"user_id", "provider", "ciphertext", "created_at", "updated_at"}
        primary_key = inspector.get_pk_constraint("provider_credentials")
        assert primary_key["constrained_columns"] == ["user_id", "provider"]
    finally:
        engine.dispose()
