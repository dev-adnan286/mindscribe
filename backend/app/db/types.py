"""Custom column types.

`EmbeddingType` stores note embeddings as a native pgvector `vector(dim)` column on
PostgreSQL and as a JSON list of floats on every other dialect (SQLite for local
development and tests). Application code always sees a plain `list[float]`.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine


class EmbeddingType(TypeDecorator[list[float]]):
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 256) -> None:
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        if value is None:
            return None
        return [float(x) for x in value]

    def process_result_value(self, value: Any, dialect: Dialect) -> list[float] | None:
        if value is None:
            return None
        return [float(x) for x in value]
