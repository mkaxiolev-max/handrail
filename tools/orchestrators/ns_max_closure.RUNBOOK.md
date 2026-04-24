# NS∞ Max-Omega Closure — Run-Book

**Target**: composite v3.1 92.42 (Omega-Approaching) → v3.1 ≈ 97.57 / v3.2 ≈ 97.60 (Omega-Transcendent)
**Script**: `tools/orchestrators/ns_max_closure.sh`
**State**: `~/.ns_max_closure/state/`
**Artifacts**: `artifacts/max_closure/`, `/Volumes/NSExternal/ALEXANDRIA/ledger/max_closure/<run_id>/`

## Prerequisites
- macOS (Mac Studio M4), bash 3.2 default shell
- `git`, `curl`, `node`, `python3>=3.11`, `docker`, `pytest`, `gitleaks`, `awk`
- Optional but recommended: `claude` CLI, `apalache-mc`, `git-filter-repo`, `ykman`, `xcodebuild`
- Repo checked out at `~/axiolev_runtime` on branch `integration/max-omega-20260421-191635`
- Alexandria mount live at `/Volumes/NSExternal/ALEXANDRIA`
- YubiKey serial `26116460` plugged in (hard-required for M5, M8, M14)
- All 14 Docker services healthy (preflight warns but doesn't abort)

## Expected Execution Time per Phase
| Phase | What | Wall-clock | Notes |
|-------|------|-----------|-------|
| PREFLIGHT | deps + branch + mount + YubiKey soft | ~30s | |
| M0  | security gate, gitleaks scan | 1–3 min | |
| M1  | INS-06 Calibration SFT | 20–40 min | torch optional |
| M2  | INS-03 Reversibility 100% | 25–45 min | coverage gate strict |
| M3  | INS-01 CPS action-surface | 30–60 min | AST lint is the long part |
| M4  | INS-08 Hormetic sweep | 15–30 min | |
| M5  | INS-02 NVIR gen + oracle | 40–90 min | Lean/Z3 warm-up |
| M6  | INS-04 TLA+/Apalache | 20–60 min | xfails clean if apalache absent |
| M7  | INS-05 Validator adapters | 30–60 min | |
| M8  | NS-AL proof-carrying exec | 30–60 min | 10 new tests T-070..T-079 |
| M9  | I7 tests T-060..T-069 | 20–40 min | |
| M10 | MASTER v3.2 scorer + FINAL CERT | 5–10 min | |
| M11 | full integration suite | 15–30 min | ~1018+ pytest, 21 vitest |
| M12 | Swift XCTest wire-up | 10–30 min | skipped unless opted-in |
| M13 | safe-to-push gate | 2–5 min | |
| M14 | certification ceremony | 1 min | gated behind env vars |

**Total**: ~4–8 hours end-to-end on a Mac Studio M4, most of it inside the Claude-driven codegen and test loops.

## Running
```bash
cd ~/axiolev_runtime
chmod +x tools/orchestrators/ns_max_closure.sh
# Dry run — no ceremony
tools/orchestrators/ns_max_closure.sh

# With ceremony (after all greens):
AXIOLEV_CERTIFY=1 AXIOLEV_QUORUM=2of2 \
  tools/orchestrators/ns_max_closure.sh
```

### Useful env overrides
- `PYTEST_RETRIES=3` — retries per phase gate (default 3)
- `AXIOLEV_ALLOW_SWIFT_TESTS=1` — enable M12 Swift target wire-up
- `AXIOLEV_SKIP_FILTER_REPO=0` — enable interactive history rewrite at M0 (needs TTY)
- `CLAUDE_BIN=claude CLAUDE_MODEL=claude-sonnet-4-5` — codegen CLI
- `TARGET_BRANCH=…` — override target branch

## Failure Recovery
Every phase is a file-state (`~/.ns_max_closure/state/<phase>.state`). On failure:

1. The phase marker flips to `failed` and a `FIX_REQUEST.md` lands in `artifacts/max_closure/`.
2. Last 200 lines of pytest output are captured in `~/.ns_max_closure/logs/<phase>.pytest.log`.
3. After fixing:
   - Edit the failing code/tests as advised in the FIX_REQUEST.
   - Re-run `ns_max_closure.sh`. It will skip `done` phases and resume on the failed phase.
4. To force a phase to re-run: `rm ~/.ns_max_closure/state/<phase>.state` then re-run.
5. To wipe all state (DANGEROUS — re-does everything): `rm -rf ~/.ns_max_closure/state`.

### If a phase fails after 3 pytest retries
- The script emits a `FIX_REQUEST.md` and exits non-zero. State is `failed`.
- Triage the failures into:
  - **(a) production-code bug** → fix the code; commit yourself before re-running if you want a clean boundary, or let the next phase run pick it up.
  - **(b) test-spec bug** → update the test with rationale in the commit message; include the insight ID (e.g. `INS-06`) and the specific T-number.
  - **(c) flake** → quarantine with `@pytest.mark.xfail(reason="flake-<ticket>")` + open a ticket. Do not land durable xfails without a ticket.
- Re-run `ns_max_closure.sh`. No flags needed — state resumes.

### If the YubiKey is absent at a hard gate (M5, M8, M14)
- Plug in the YubiKey (serial **26116460**). Re-run. The state file keeps all prior `done` phases intact.

### If Alexandria is unmounted
- Preflight warns and continues. Receipts are deferred (not written). Remount `NSExternal`, then re-run any phase (`rm ~/.ns_max_closure/state/<phase>.state` if you want the receipt this run).

### If `axiolev_push.sh --dry-run` fails at M13
- Inspect `~/.ns_max_closure/logs/M13.push.log`. The push wrapper never force-pushes master; typical issues are diverged remote or missing upstream. Fix upstream manually (`git fetch; git rebase` etc.), then re-run.

## Resuming from Checkpoint
```bash
# Inspect state
ls -1 ~/.ns_max_closure/state/
for f in ~/.ns_max_closure/state/*.state; do
  printf "%-14s %s\n" "$(basename "$f" .state)" "$(head -n1 "$f")"
done

# Resume
tools/orchestrators/ns_max_closure.sh
```

## Ontology Compliance
Use only the canonical names: **Gradient Field, Alexandrian Lexicon, State Manifold, Alexandrian Archive, Lineage Fabric, Narrative**. Deprecated (FORBIDDEN): Ether, Lexicon (alone), CTF, Storytime-as-layer. Every phase runs `ontology_guard` which greps for forbidden terms and warns on hits.

## Tag Catalog Produced
- `ins-06-calibration-sft-v1` `ins-03-reversibility-complete-v1` `ins-01-cps-action-surface-v1`
- `ins-08-hormetic-sweep-v1` `ins-02-nvir-generator-v1` `ins-04-tla-apalache-v1`
- `ins-05-validators-v1` `ns-al-assurance-live-v1` `i7-category-tests-v1`
- `master-v32-final-cert-v1` `swift-xctest-wired-v1` (optional)
- On ceremony: `ns-infinity-max-omega-certified-<YYYYMMDD>` + `ns-infinity-supermax-complete-v1.0.0`
