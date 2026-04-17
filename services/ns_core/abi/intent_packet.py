"""IntentPacket.v1 — ABI-frozen extension of models.IntentPacket."""
from __future__ import annotations

from typing import Literal

from models.intent_packet import IntentPacket as _Base


class IntentPacket(_Base):
    schema_version: Literal[1] = 1
    dignity_banner: Literal[
        "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    ] = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
