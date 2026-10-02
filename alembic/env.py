import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from cashevide_api.config import settings
from cashevide_api.database import Base
from cashevide_api.users.models import BlacklistedToken, User, UserProfile  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


# NOTE: This is a temporary bridge for the Django → FastAPI migration.
# Django's database currently has many tables (invoices_*, clients_*,
# catalog_*, etc.) that don't have FastAPI/SQLAlchemy models yet. Without
# this filter, Alembic would see those tables as "should be removed" and
# generate migrations that DROP them — which would destroy production data.
#
# As each Django app gets ported to a FastAPI model (the way `users` was),
# that table becomes known to Alembic and this filter stops affecting it.
# Once every table has a corresponding model, this function will never
# actually exclude anything — at that point it's safe to delete this
# function entirely (and remove `include_object=include_object` below).
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
