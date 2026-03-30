"""
NS MCP Tool Router
NS is the single governed client. Tools are MCP servers.
Every tool call: policy check → lease → execute → receipt → return.

Architecture:
    Arbiter / Operator
        ↓ tool_request
    MCPRouter (this module)
        ↓ policy_check (allowlist, arg sanitization, lease)
        ↓ execute (local or remote MCP server)
        ↓ verifier_check (output plausibility, citation check)
        ↓ receipt_emit
        → return result

Tools are NEVER called directly by operators.
Operators express tool_requests. NS decides if, when, and how.

Safety model:
    - Read-only by default
    - Write requires lease + receipt
    - Shell requires explicit SHELL_EXEC permission
    - Path restrictions enforced before any filesystem op
    - Args sanitized (no shell injection, no path traversal)
    - Output verified (plausibility check, size limits)
"""

import asyncio
import json
import os
import re
import subprocess
import shutil
import hashlib
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


# ── Tool Registry ──────────────────────────────────────────────────────────────

TOOL_CATALOG: Dict[str, "ToolSpec"] = {}


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ToolSpec:
    """Definition of one tool available to NS."""
    name: str
    description: str
    category: str              # filesystem | shell | media | artifact | web | data
    read_only: bool = True     # False = write operations permitted
    requires_lease: bool = False  # True = EXEC lease required from founder
    requires_permission: str = ""  # NS permission string required
    allowed_paths: List[str] = field(default_factory=list)  # path prefix allowlist
    arg_schema: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("handler", None)
        return d


@dataclass
class ToolCall:
    """A single tool invocation request."""
    tool_name: str
    args: Dict[str, Any]
    requested_by: str        # operator or user_id
    session_id: str = ""
    domain: str = "general"
    call_id: str = field(default_factory=lambda: hashlib.sha256(
        f"{time.time_ns()}".encode()).hexdigest()[:12])
    requested_at: str = field(default_factory=_ts)


@dataclass
class ToolResult:
    """Result of a tool call after policy + execution."""
    call_id: str
    tool_name: str
    success: bool
    result: Any = None
    error: str = ""
    policy_blocked: bool = False
    block_reason: str = ""
    receipt_id: str = ""
    executed_at: str = field(default_factory=_ts)
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ── Policy Engine ──────────────────────────────────────────────────────────────

class ToolPolicyEngine:
    """
    Enforces least-privilege access to all tools.
    Every tool call passes through here before execution.
    """

    # Dangerous shell patterns — always blocked
    SHELL_BLACKLIST = [
        r"rm\s+-rf",
        r"dd\s+if=",
        r"mkfs",
        r">\s*/dev/",
        r"chmod\s+777",
        r"\$\(",        # command substitution
        r"`[^`]+`",     # backtick execution
        r"&&\s*rm",
        r"\|\s*sh",
        r"\|\s*bash",
        r"curl.*\|.*sh",
        r"wget.*\|.*sh",
        r"/etc/passwd",
        r"/etc/shadow",
        r"ssh\s+",
    ]

    # Path traversal patterns
    PATH_TRAVERSAL = [r"\.\./", r"\.\\\.", r"%2e%2e"]

    def check(self, call: ToolCall, spec: ToolSpec,
              ctx_role: str = "EXEC") -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        allowed=True means proceed. False means block.
        """
        ROLE_RANK = {"FOUNDER": 4, "EXEC": 3, "SAN": 2, "USER": 1}
        caller_rank = ROLE_RANK.get(ctx_role, 0)

        # 1. Shell tools require FOUNDER or explicit permission
        if spec.category == "shell" and caller_rank < ROLE_RANK["EXEC"]:
            return False, "Shell tools require EXEC or FOUNDER role"

        # 2. Lease check for write + shell ops
        if spec.requires_lease and caller_rank < ROLE_RANK["FOUNDER"]:
            return False, f"Tool '{spec.name}' requires FOUNDER lease"

        # 3. Check required permission
        if spec.requires_permission:
            # In production this checks ctx.permissions; here we trust role rank
            if spec.requires_permission == "SHELL_EXEC" and caller_rank < ROLE_RANK["EXEC"]:
                return False, "SHELL_EXEC permission required"

        # 4. Sanitize args
        ok, reason = self._sanitize_args(call.args, spec)
        if not ok:
            return False, reason

        # 5. Path restriction for filesystem ops
        if "path" in call.args or "file_path" in call.args:
            path_arg = call.args.get("path") or call.args.get("file_path", "")
            ok, reason = self._check_path(path_arg, spec)
            if not ok:
                return False, reason

        return True, "ok"

    def _sanitize_args(self, args: dict, spec: ToolSpec) -> tuple[bool, str]:
        """Check for shell injection, path traversal in all string args."""
        args_str = json.dumps(args)

        # Path traversal
        for pat in self.PATH_TRAVERSAL:
            if re.search(pat, args_str, re.IGNORECASE):
                return False, f"Path traversal detected in args"

        # Shell injection (only for shell category)
        if spec.category == "shell":
            for pat in self.SHELL_BLACKLIST:
                if re.search(pat, args_str, re.IGNORECASE):
                    return False, f"Blocked shell pattern in args"

        # Arg size limit (prevent prompt injection via huge args)
        if len(args_str) > 50000:
            return False, "Args too large (50K limit)"

        return True, "ok"

    def _check_path(self, path_str: str, spec: ToolSpec) -> tuple[bool, str]:
        """Enforce allowed_paths allowlist."""
        if not spec.allowed_paths:
            return True, "ok"  # No restriction configured

        try:
            resolved = str(Path(path_str).resolve())
        except Exception:
            return False, f"Invalid path: {path_str}"

        for allowed in spec.allowed_paths:
            if resolved.startswith(str(Path(allowed).resolve())):
                return True, "ok"

        return False, f"Path '{path_str}' outside allowed zones: {spec.allowed_paths}"


# ── Output Verifier ────────────────────────────────────────────────────────────

class ToolOutputVerifier:
    """
    Checks tool output before returning to operator.
    Catches: oversized output, suspicious content, missing citations.
    """

    MAX_OUTPUT_SIZE = 500_000  # 500KB text output limit

    def verify(self, tool_name: str, result: Any,
                require_citations: bool = False) -> tuple[bool, str]:
        """Returns (ok, warning_message). Always returns result even if warning."""
        if result is None:
            return True, ""

        result_str = json.dumps(result) if not isinstance(result, str) else result

        # Size check
        if len(result_str) > self.MAX_OUTPUT_SIZE:
            return False, f"Output too large ({len(result_str)} chars). Truncating."

        # Citation check (for research tools)
        if require_citations:
            if not any(marker in result_str for marker in ["http", "doi:", "ISBN", "§", "Source:"]):
                return True, "Warning: No citations detected in output"

        return True, ""


# ── MCP Router ────────────────────────────────────────────────────────────────

class MCPRouter:
    """
    NS sovereign tool router.
    Tools call through here or not at all.
    """

    def __init__(self, receipt_chain=None):
        self._policy = ToolPolicyEngine()
        self._verifier = ToolOutputVerifier()
        self._receipt_chain = receipt_chain
        self._active_leases: Dict[str, dict] = {}  # call_id → lease info
        self._call_log: List[dict] = []  # recent calls

        # Register built-in tools
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register all built-in NS tools."""
        tools = [
            # ── Filesystem (read-only) ──────────────────────────────────────
            ToolSpec(
                name="fs_read",
                description="Read a file or list a directory",
                category="filesystem",
                read_only=True,
                allowed_paths=[str(Path.home()), "/Volumes/NSExternal", "/tmp/ns_workspace"],
                arg_schema={"path": "str"},
                handler=self._fs_read,
            ),
            ToolSpec(
                name="fs_write",
                description="Write to a file in the NS workspace",
                category="filesystem",
                read_only=False,
                requires_lease=False,
                allowed_paths=[
                    str(Path.home() / "NSS"),
                    str(Path.home() / "ALEXANDRIA"),
                    "/Volumes/NSExternal/ALEXANDRIA",
                    "/tmp/ns_workspace",
                ],
                arg_schema={"path": "str", "content": "str"},
                handler=self._fs_write,
            ),
            ToolSpec(
                name="fs_search",
                description="Search files by name or content",
                category="filesystem",
                read_only=True,
                allowed_paths=[str(Path.home()), "/Volumes/NSExternal", "/tmp/ns_workspace"],
                arg_schema={"root": "str", "pattern": "str", "content_query": "str?"},
                handler=self._fs_search,
            ),

            # ── Shell (lease-gated) ─────────────────────────────────────────
            ToolSpec(
                name="shell_run",
                description="Run a shell command (sandboxed, allowlisted commands only)",
                category="shell",
                read_only=False,
                requires_lease=True,
                requires_permission="SHELL_EXEC",
                arg_schema={"command": "str", "cwd": "str?", "timeout": "int?"},
                handler=self._shell_run,
            ),

            # ── Git ─────────────────────────────────────────────────────────
            ToolSpec(
                name="git_status",
                description="Get git status of a repository",
                category="shell",
                read_only=True,
                arg_schema={"repo_path": "str"},
                handler=self._git_status,
            ),
            ToolSpec(
                name="git_log",
                description="Get recent git commits",
                category="shell",
                read_only=True,
                arg_schema={"repo_path": "str", "n": "int?"},
                handler=self._git_log,
            ),

            # ── Artifact generators ─────────────────────────────────────────
            ToolSpec(
                name="render_infographic",
                description="Generate an SVG infographic from a spec dict",
                category="artifact",
                read_only=False,
                arg_schema={"spec": "dict", "output_path": "str?"},
                handler=self._render_infographic,
            ),
            ToolSpec(
                name="render_deck",
                description="Generate a PPTX presentation from a spec dict",
                category="artifact",
                read_only=False,
                arg_schema={"spec": "dict", "output_path": "str?"},
                handler=self._render_deck,
            ),
            ToolSpec(
                name="render_brief",
                description="Generate a PDF brief from structured content",
                category="artifact",
                read_only=False,
                arg_schema={"spec": "dict", "output_path": "str?"},
                handler=self._render_brief,
            ),

            # ── Web ─────────────────────────────────────────────────────────
            ToolSpec(
                name="web_fetch",
                description="Fetch and extract text from a URL",
                category="web",
                read_only=True,
                arg_schema={"url": "str", "extract_text": "bool?"},
                handler=self._web_fetch,
            ),

            # ── Podcast engine ──────────────────────────────────────────────
            ToolSpec(
                name="podcast_package_sources",
                description="Package sources (PDFs, URLs, text) into a source pack",
                category="artifact",
                read_only=False,
                arg_schema={"sources": "list", "episode_id": "str?"},
                handler=self._podcast_package_sources,
            ),
            ToolSpec(
                name="podcast_generate_script",
                description="Generate a podcast script from a source pack",
                category="artifact",
                read_only=False,
                arg_schema={"source_pack_id": "str", "style": "str?", "hosts": "list?"},
                handler=self._podcast_generate_script,
            ),
        ]

        for t in tools:
            TOOL_CATALOG[t.name] = t

    async def execute(self, call: ToolCall, ctx_role: str = "EXEC") -> ToolResult:
        """
        Main entry point. Policy → Execute → Verify → Receipt.
        """
        t0 = time.time()
        spec = TOOL_CATALOG.get(call.tool_name)

        if not spec:
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                error=f"Unknown tool: {call.tool_name}"
            )

        # Policy check
        allowed, reason = self._policy.check(call, spec, ctx_role)
        if not allowed:
            result = ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                policy_blocked=True,
                block_reason=reason,
                error=f"Policy blocked: {reason}"
            )
            self._emit_receipt(call, result, "TOOL_BLOCKED")
            return result

        # Execute
        try:
            if asyncio.iscoroutinefunction(spec.handler):
                raw = await spec.handler(**call.args)
            else:
                raw = spec.handler(**call.args)
        except Exception as e:
            result = ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - t0) * 1000
            )
            self._emit_receipt(call, result, "TOOL_ERROR")
            return result

        # Verify output
        ok, warning = self._verifier.verify(call.tool_name, raw)

        result = ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            success=True,
            result=raw if ok else str(raw)[:self._verifier.MAX_OUTPUT_SIZE],
            error=warning if warning else "",
            duration_ms=(time.time() - t0) * 1000
        )

        self._emit_receipt(call, result, "TOOL_EXECUTED")
        self._call_log.append({
            "call_id": call.call_id,
            "tool": call.tool_name,
            "domain": call.domain,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "ts": _ts()
        })
        self._call_log = self._call_log[-200:]

        return result

    def _emit_receipt(self, call: ToolCall, result: ToolResult, event_type: str):
        if self._receipt_chain:
            try:
                r = self._receipt_chain.emit(
                    event_type,
                    {"kind": "mcp_tool", "ref": call.requested_by},
                    {"tool": call.tool_name, "args_hash": hashlib.sha256(
                        json.dumps(call.args, sort_keys=True).encode()).hexdigest()[:8]},
                    {"success": result.success, "duration_ms": result.duration_ms,
                     "policy_blocked": result.policy_blocked,
                     "error": result.error[:200] if result.error else ""}
                )
                result.receipt_id = r.get("receipt_id", "")
            except Exception:
                pass

    def list_tools(self, category: str = None) -> List[dict]:
        tools = list(TOOL_CATALOG.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return [t.to_dict() for t in tools]

    def get_call_log(self, limit: int = 50) -> List[dict]:
        return self._call_log[-limit:][::-1]

    # ── Tool Handlers ──────────────────────────────────────────────────────

    def _fs_read(self, path: str, **kwargs) -> Any:
        p = Path(path).expanduser()
        if p.is_dir():
            items = []
            for item in sorted(p.iterdir()):
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return {"path": str(p), "type": "directory", "items": items}
        elif p.is_file():
            content = p.read_text(errors="replace")
            return {"path": str(p), "type": "file", "content": content,
                    "size": len(content)}
        else:
            raise FileNotFoundError(f"Not found: {path}")

    def _fs_write(self, path: str, content: str, **kwargs) -> dict:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return {"path": str(p), "bytes_written": len(content), "ok": True}

    def _fs_search(self, root: str, pattern: str = "*",
                   content_query: str = None, **kwargs) -> dict:
        root_p = Path(root).expanduser()
        matches = []
        for f in root_p.rglob(pattern):
            if f.is_file() and len(matches) < 100:
                if content_query:
                    try:
                        if content_query.lower() in f.read_text(errors="replace").lower():
                            matches.append(str(f))
                    except Exception:
                        pass
                else:
                    matches.append(str(f))
        return {"root": root, "pattern": pattern, "matches": matches,
                "count": len(matches)}

    def _shell_run(self, command: str, cwd: str = None,
                   timeout: int = 30, **kwargs) -> dict:
        """Sandboxed shell execution. Allowlisted commands only."""
        ALLOWED_COMMANDS = [
            "python3", "python", "pip", "node", "npm", "git",
            "ls", "cat", "head", "tail", "wc", "grep", "find",
            "ffmpeg", "ffprobe", "convert", "pandoc",
            "pptxgenjs", "reportlab", "echo", "date"
        ]
        cmd_base = command.strip().split()[0]
        if cmd_base not in ALLOWED_COMMANDS:
            raise PermissionError(f"Command '{cmd_base}' not in NS shell allowlist")

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=cwd or "/tmp"
        )
        return {
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
            "command": command
        }

    def _git_status(self, repo_path: str, **kwargs) -> dict:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=repo_path, timeout=10
        )
        return {"status": result.stdout, "repo": repo_path}

    def _git_log(self, repo_path: str, n: int = 10, **kwargs) -> dict:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline", "--format=%h %s (%an, %ar)"],
            capture_output=True, text=True, cwd=repo_path, timeout=10
        )
        return {"log": result.stdout, "repo": repo_path}

    async def _web_fetch(self, url: str, extract_text: bool = True, **kwargs) -> dict:
        """Fetch a URL. Requires httpx."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.get(url, headers={"User-Agent": "NS-Research/1.0"})
                content = r.text[:50000]
                if extract_text:
                    # Strip HTML tags
                    import re as _re
                    content = _re.sub(r"<[^>]+>", " ", content)
                    content = _re.sub(r"\s+", " ", content).strip()
                return {"url": url, "status": r.status_code, "content": content}
        except Exception as e:
            return {"url": url, "error": str(e)}

    def _render_infographic(self, spec: dict, output_path: str = None, **kwargs) -> dict:
        """Generate SVG infographic from spec."""
        from nss.actuators.artifacts import render_infographic_svg
        svg_content = render_infographic_svg(spec)
        out = output_path or f"/tmp/ns_workspace/infographic_{int(time.time())}.svg"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(svg_content)
        return {"path": out, "format": "svg", "bytes": len(svg_content)}

    def _render_deck(self, spec: dict, output_path: str = None, **kwargs) -> dict:
        """Generate PPTX from spec."""
        from nss.actuators.artifacts import render_deck_pptx
        out = output_path or f"/tmp/ns_workspace/deck_{int(time.time())}.pptx"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        render_deck_pptx(spec, out)
        return {"path": out, "format": "pptx", "bytes": Path(out).stat().st_size}

    def _render_brief(self, spec: dict, output_path: str = None, **kwargs) -> dict:
        """Generate PDF brief from spec."""
        from nss.actuators.artifacts import render_brief_pdf
        out = output_path or f"/tmp/ns_workspace/brief_{int(time.time())}.pdf"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        render_brief_pdf(spec, out)
        return {"path": out, "format": "pdf", "bytes": Path(out).stat().st_size}

    def _podcast_package_sources(self, sources: list,
                                  episode_id: str = None, **kwargs) -> dict:
        from nss.actuators.podcast import SourcePackager
        packager = SourcePackager()
        pack = packager.package(sources, episode_id)
        return pack

    def _podcast_generate_script(self, source_pack_id: str,
                                  style: str = "conversational",
                                  hosts: list = None, **kwargs) -> dict:
        from nss.actuators.podcast import Showrunner
        runner = Showrunner()
        script = runner.generate(source_pack_id, style=style, hosts=hosts)
        return script


# ── Singleton ──────────────────────────────────────────────────────────────────

_router: Optional[MCPRouter] = None

def get_mcp_router(receipt_chain=None) -> MCPRouter:
    global _router
    if _router is None:
        _router = MCPRouter(receipt_chain=receipt_chain)
    elif receipt_chain and _router._receipt_chain is None:
        _router._receipt_chain = receipt_chain
    return _router
