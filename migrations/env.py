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

# Alembic config is available at runtime inside context; do not access it at import time.
# Configure logging if alembic.ini is present (this is safe; fileConfig will no-op if not used by CLI)
cfg_file = None
try:
    cfg_file = context.config.config_file_name
except Exception:
    cfg_file = None

if cfg_file:
    fileConfig(cfg_file)

# Import the application's db and model modules so metadata is available.
# Adjust these import paths if your project layout differs.
try:
    from app.extensions import db
except Exception as e:
    raise RuntimeError(
        "Failed to import `db` from app.extensions. Ensure app/extensions.py exists "
        "and re-exports the db instance (e.g., `from app.authanduser.extensions import db`)."
    ) from e

try:
    # Import modules that define models so they register on db.metadata
    from app.authanduser import models  # adjust if your models live elsewhere
except Exception as e:
    raise RuntimeError(
        "Failed to import model modules (app.authanduser.models). "
        "Ensure model modules import the same `db` instance and do not create the app on import."
    ) from e

target_metadata = getattr(db, "metadata", None)
if target_metadata is None:
    raise RuntimeError("Imported `db` does not expose `metadata`. Ensure `db = SQLAlchemy()` is defined.")

# If metadata has no tables, raise a helpful error (prevents silent autogenerate failures)
if not list(target_metadata.tables.keys()):
    raise RuntimeError(
        "No tables were registered on db.metadata at import time. "
        "Common causes: model modules not imported here, models using a different SQLAlchemy instance, "
        "or model imports causing errors. Ensure models import the same `db` and are imported above."
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

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
