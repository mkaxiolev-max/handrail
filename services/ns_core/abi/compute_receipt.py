"""ComputeReceipt.v1 — ABI-frozen extension of models.ComputeReceipt."""
from __future__ import annotations

from typing import Literal

from models.compute_receipt import ComputeReceipt as _Base


class ComputeReceipt(_Base):
    schema_version: Literal[1] = 1
    dignity_banner: Literal[
        "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    ] = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
