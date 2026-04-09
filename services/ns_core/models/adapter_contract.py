from pydantic import BaseModel
from typing import List


class AdapterContract(BaseModel):
    """Unified driver interface for all I/O."""
    adapter_type: str  # voice, http, process, fs, db, mac
    adapter_name: str
    contract_version: str
    capabilities: List[str]
    required_permissions: List[str]
    timeout_ms: int
    max_retries: int
