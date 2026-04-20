# Secret Remediation Findings

Generated: 2026-04-20T00:52Z

## Secret type
GitHub Personal Access Token (ghp_* pattern) — ALREADY REVOKED by GitHub.

## Working tree exposures (2 files, 4 lines)
- .terminal_manager/state/state_20260416T233746Z.md  (lines 107-108)
- .terminal_manager/state/state_20260416T234033Z.md  (lines 107-108)
Both files contain `git remote -v` output copied verbatim into state snapshots.

## Git history exposures (2 commits, many files)
- commit 67ef55f  (ring-1: L1 constitutional layer)
  Files: .terminal_manager/state/*.json, *.jsonl, *.log, *.sh, *.md
  Source: `git remote -v` output captured into terminal manager snapshots.

- commit c492926  (omega-Z3: Omega L10 primitives)
  Files: remediation script containing the token in example/regex patterns.

## Other secret-like patterns
- STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, TWILIO_AUTH_TOKEN all load from
  os.environ — no actual values committed. Safe.
- artifacts/gitleaks_20260419T224057Z.json references ALPACA_SECRET_KEY=REDACTED
  (already redacted value). Safe.

## Scope of history rewrite required
Token appears in diff of 2 commits out of 363. git-filter-repo will replace
the raw token string with REMOVED_GITHUB_SECRET across all blobs in all commits.
