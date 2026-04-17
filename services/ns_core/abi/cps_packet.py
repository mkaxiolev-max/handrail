"""CPSPacket.v1 — ABI-frozen extension of models.CPSPacket."""
from __future__ import annotations

from typing import Literal

from models.cps_packet import CPSPacket as _Base


class CPSPacket(_Base):
    schema_version: Literal[1] = 1
    dignity_banner: Literal[
        "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
    ] = "AXIOLEV HOLDINGS LLC — DIGNITY PRESERVED"
