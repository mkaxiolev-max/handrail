from __future__ import annotations
from typing import Optional
from .models import HyperObject, HyperObjectID

class HyperObjectStore:
    def __init__(self):
        self._store: dict[HyperObjectID, HyperObject] = {}

    def create(self, obj: HyperObject) -> HyperObject:
        self._store[obj.id] = obj
        return obj

    def read(self, obj_id: HyperObjectID) -> Optional[HyperObject]:
        return self._store.get(obj_id)

    def write_versioned(self, obj: HyperObject) -> HyperObject:
        updated = obj.bump_version()
        self._store[updated.id] = updated
        return updated

    def list_all(self) -> list[HyperObject]:
        return list(self._store.values())

    def count(self) -> int:
        return len(self._store)

_store = HyperObjectStore()
def get_store() -> HyperObjectStore:
    return _store
