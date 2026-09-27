"""initial multi-database schema

Revision ID: 0001_initial_multidb_schema
Revises:
Create Date: 2026-08-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

from app.db.base import RealBase, SecurityBase, SyntheticBase
from app.db.engines import get_real_engine, get_security_engine, get_synthetic_engine
from app.models import real as real_models  # noqa: F401
from app.models import security as security_models  # noqa: F401
from app.models import synthetic as synthetic_models  # noqa: F401

# revision identifiers, used by Alembic.
revision = "0001_initial_multidb_schema"
down_revision = None
branch_labels = None
depends_on = None


def _current_engine_name() -> str:
    context = op.get_context()
    engine_name = context.config.attributes.get("engine_name")
    if not engine_name:
        raise RuntimeError("Alembic engine_name is missing; use the bundled env.py to run migrations.")
    return engine_name


def _engine_and_metadata() -> tuple[object, object]:
    engine_name = _current_engine_name()
    if engine_name == "real":
        return get_real_engine(), RealBase.metadata
    if engine_name == "synthetic":
        return get_synthetic_engine(), SyntheticBase.metadata
    if engine_name == "security":
        return get_security_engine(), SecurityBase.metadata
    raise RuntimeError(f"Unknown Alembic engine_name: {engine_name}")


def upgrade() -> None:
    engine, metadata = _engine_and_metadata()
    metadata.create_all(bind=engine)


def downgrade() -> None:
    engine, metadata = _engine_and_metadata()
    metadata.drop_all(bind=engine)