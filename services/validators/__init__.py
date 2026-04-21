"""Validator adapter contracts — AXIOLEV © 2026."""
from typing import Protocol

class Validator(Protocol):
    domain: str
    def validate(self, candidate: dict) -> dict: ...

class LeanAdapter:
    domain = "math"
    def validate(self, candidate: dict) -> dict:
        return {"ok": False, "reason": "lean adapter stub"}

class DFTAdapter:
    domain = "materials"
    def validate(self, candidate: dict) -> dict:
        return {"ok": False, "reason": "dft adapter stub"}

class FDAClassAdapter:
    domain = "clinical"
    def validate(self, candidate: dict) -> dict:
        return {"ok": False, "reason": "fda-class adapter stub"}

REGISTRY = {"math": LeanAdapter(), "materials": DFTAdapter(), "clinical": FDAClassAdapter()}
