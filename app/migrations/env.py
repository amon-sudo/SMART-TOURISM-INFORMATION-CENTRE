# app/migrations/env.py
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure project root is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure logging only if alembic.ini is present at runtime
cfg_file = None
try:
    cfg_file = context.config.config_file_name
except Exception:
    cfg_file = None

if cfg_file:
    fileConfig(cfg_file)

# Import the application's db and model modules so metadata is available.
try:
    from app.extensions import db
except Exception as e:
    raise RuntimeError(
        "Failed to import `db` from app.extensions. Ensure app/extensions.py exists "
        "and re-exports the db instance (e.g., `from app.authanduser.extensions import db`)."
    ) from e

try:
    from app.authanduser import models
except Exception as e:
    raise RuntimeError(
        "Failed to import model modules (app.authanduser.models). "
        "Ensure model modules import the same `db` instance and do not create the app on import."
    ) from e

target_metadata = getattr(db, "metadata", None)
if target_metadata is None:
    raise RuntimeError("Imported `db` does not expose `metadata`. Ensure `db = SQLAlchemy()` is defined.")

if not list(target_metadata.tables.keys()):
    raise RuntimeError(
        "No tables were registered on db.metadata at import time. "
        "Ensure models import the same `db` and are imported above."
    )

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL)."""
    cfg = context.config
    url = cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (apply to DB)."""
    cfg = context.config
    connectable = engine_from_config(
        cfg.get_section(cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

# Call migration runner only when the Alembic EnvironmentContext proxy is available.
# When this file is imported for diagnostics (via importlib), the proxy may not be established
# and calling context.is_offline_mode() raises a NameError. Handle that case gracefully.
try:
    is_offline = context.is_offline_mode()
except NameError:
    # proxy not established (imported for diagnostics) — do not attempt to run migrations here
    is_offline = None

if is_offline is True:
    run_migrations_offline()
elif is_offline is False:
    run_migrations_online()
# if is_offline is None, we were imported for inspection; do nothing
