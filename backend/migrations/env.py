from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.base import RealBase, SecurityBase, SyntheticBase  # noqa: E402
from app.db.engines import get_real_engine, get_security_engine, get_synthetic_engine  # noqa: E402
from app.models import real as real_models  # noqa: F401,E402
from app.models import security as security_models  # noqa: F401,E402
from app.models import synthetic as synthetic_models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

TARGETS = {
    "real": (get_real_engine(), RealBase.metadata),
    "synthetic": (get_synthetic_engine(), SyntheticBase.metadata),
    "security": (get_security_engine(), SecurityBase.metadata),
}


def run_migrations_offline() -> None:
    raise RuntimeError("Offline Alembic migrations are not supported for the multi-database setup.")


def run_migrations_online() -> None:
    for name, (engine, metadata) in TARGETS.items():
        config.attributes["engine_name"] = name
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=metadata,
                version_table=f"alembic_version_{name}",
                compare_type=True,
                render_as_batch=connection.dialect.name == "sqlite",
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()