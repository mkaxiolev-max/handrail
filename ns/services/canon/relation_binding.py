"""Canon relation binding — records directed relationships between canon entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RelationBinding:
    subject: str
    predicate: str
    object_: Any
    canon_ref: str = ""
    tick: int = 0


class RelationBinder:
    """Append-only binder for canon relation records (I2)."""

    def __init__(self) -> None:
        self._bindings: list[RelationBinding] = []

    def bind(self, subject: str, predicate: str, object_: Any, canon_ref: str = "") -> RelationBinding:
        binding = RelationBinding(
            subject=subject,
            predicate=predicate,
            object_=object_,
            canon_ref=canon_ref,
            tick=len(self._bindings) + 1,
        )
        self._bindings.append(binding)
        return binding

    def all_bindings(self) -> list[RelationBinding]:
        return list(self._bindings)
