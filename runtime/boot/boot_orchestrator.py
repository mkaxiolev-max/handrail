from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runtime.boot.ancestry_retrieval import retrieve_minimal_ancestry
from runtime.boot.coherence_scan import run_coherence_scan
from runtime.boot.infra_boot import collect_infra_boot
from runtime.boot.operating_frame import build_operating_frame
from runtime.boot.present_state import synthesize_present_state
from runtime.handrail_bridge.task_packet_builder import build_execution_packet


def now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def write_json(path: Path, obj) -> None:
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
    else:
        data = obj
    path.write_text(json.dumps(data, indent=2))


def main() -> int:
    workspace = Path.cwd()
    runs_root = Path("/Volumes/NSExternal/.run/boot")
    runs_root.mkdir(parents=True, exist_ok=True)

    run_id = now_id()
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    infra = collect_infra_boot(run_id=run_id, run_dir=run_dir, workspace=workspace)
    write_json(run_dir / "infra_boot_report.json", infra)

    present = synthesize_present_state(infra)
    write_json(run_dir / "present_state_kernel.json", present)

    ancestry = retrieve_minimal_ancestry(run_id=run_id, present_state=present)
    write_json(run_dir / "ancestry_graph.json", ancestry)

    coherence = run_coherence_scan(run_id=run_id, present_state=present, ancestry=ancestry)
    write_json(run_dir / "coherence_report.json", coherence)

    operating_frame = build_operating_frame(
        run_id=run_id,
        present_state=present,
        ancestry=ancestry,
        coherence=coherence,
    )
    write_json(run_dir / "operating_frame.json", operating_frame)

    execution_packet = build_execution_packet(
        operating_frame=operating_frame,
        objective="produce boot run bundle and runtime diff"
    )
    write_json(run_dir / "execution_packet.json", execution_packet)

    (runs_root / "latest_present_state_boot").write_text(str(run_dir) + "\n")

    print(json.dumps({
        "ok": True,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "artifacts": [
            "infra_boot_report.json",
            "present_state_kernel.json",
            "ancestry_graph.json",
            "coherence_report.json",
            "operating_frame.json",
            "execution_packet.json",
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
