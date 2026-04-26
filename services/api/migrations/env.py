from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.core.database import Base

config = context.config
# Alembic uses ConfigParser interpolation; escape percent signs from URL-encoded credentials.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC.replace("%", "%%"))

#config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
