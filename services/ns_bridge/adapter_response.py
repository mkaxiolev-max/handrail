from enum import Enum
from typing import Any, Dict
from datetime import datetime
class AdapterStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DEGRADED = "degraded"
class CanonicalAdapterResponse:
    def __init__(self, command: str, status: AdapterStatus, ok: bool, output: Dict[str, Any] = None, output_ok: bool = True, errors: list = None):
        self.command = command
        self.status = status
        self.ok = ok
        self.output = output or {}
        self.output_ok = output_ok
        self.errors = errors or []
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self._validate()
    def _validate(self):
        if not isinstance(self.ok, bool):
            raise ValueError(f"ok must be bool, got {type(self.ok).__name__}")
        if not isinstance(self.output_ok, bool):
            raise ValueError(f"output_ok must be bool, got {type(self.output_ok).__name__}")
        if self.output is None:
            raise ValueError("output cannot be None")
        if not isinstance(self.errors, list):
            raise ValueError("errors must be list")
    def to_dict(self) -> Dict:
        return {"command": self.command, "status": self.status.value, "ok": self.ok, "output": self.output, "output_ok": self.output_ok, "errors": self.errors, "timestamp": self.timestamp}
def git_status_response(returncode: int, stdout: str, stderr: str) -> CanonicalAdapterResponse:
    return CanonicalAdapterResponse(command="git.status", status=AdapterStatus.SUCCESS if returncode == 0 else AdapterStatus.FAILURE, ok=(returncode == 0), output={"returncode": returncode, "stdout": stdout, "stderr": stderr}, output_ok=(returncode == 0), errors=[stderr] if stderr else [])
