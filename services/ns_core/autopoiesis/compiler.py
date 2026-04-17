"""Document-to-Program compiler."""
from __future__ import annotations

import re
from typing import Any, Dict


class ProgramSpec:
    def __init__(self, name: str, ops: list, metadata: Dict[str, Any]):
        self.name = name
        self.ops = ops
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "ops": self.ops, "metadata": self.metadata}


class DocumentCompiler:
    """Compile a plain-text document or dict into a ProgramSpec."""

    def compile(self, doc: Any) -> ProgramSpec:
        if isinstance(doc, dict):
            return ProgramSpec(
                name=doc.get("name", "unnamed"),
                ops=doc.get("ops", []),
                metadata={k: v for k, v in doc.items() if k not in ("name", "ops")},
            )
        if isinstance(doc, str):
            name_match = re.search(r"(?:name|program)[:=]\s*(\S+)", doc, re.I)
            name = name_match.group(1) if name_match else "unnamed"
            ops = re.findall(r"\bop[:=]\s*(\S+)", doc, re.I)
            return ProgramSpec(name=name, ops=ops, metadata={"source": "text"})
        raise ValueError(f"unsupported doc type: {type(doc)}")
