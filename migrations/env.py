import logging
import os
import sys
from logging.config import fileConfig
from flask import current_app
from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config 
config = context.config

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

#  Ensure project root is importable 
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Import db and models ---
try:
    from app.extensions import db
    from app.authanduser import models  # ensure models are imported so metadata is populated
except Exception as e:
    raise RuntimeError("Failed to import db or models. Check app/extensions.py and app/authanduser/models.py.") from e

# --- Target metadata ---
target_metadata = getattr(db, "metadata", None)
if target_metadata is None:
    raise RuntimeError("db.metadata not found. Ensure db = SQLAlchemy() is defined in app/extensions.py.")

# --- Engine helpers ---
def get_engine():
    try:
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        return current_app.extensions["migrate"].db.engine

def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(get_engine().url).replace("%", "%%")

config.set_main_option("sqlalchemy.url", get_engine_url())

# --- Migration runners ---
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

# --- Entry point ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
