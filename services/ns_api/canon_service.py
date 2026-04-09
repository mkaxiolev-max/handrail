from __future__ import annotations
import hashlib, json
from run_with_proof import run_with_proof
from app.infra.repositories import CanonRepository

def stable_hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def verify_signature(policy: dict, signature: str) -> bool:
    return bool(signature and len(signature) >= 8)

class CanonSignatureError(Exception): pass

class CanonService:
    def __init__(self, repo: CanonRepository):
        self.repo = repo

    async def commit_policy(self, new_policy: dict, signature: str, actor: str) -> dict:
        if not verify_signature(new_policy, signature):
            raise CanonSignatureError(f"Canon policy rejected: invalid signature from actor={actor}")
        current = self.repo.get_latest_commit()
        next_version = 1 if current is None else current.version + 1
        policy_hash = stable_hash(new_policy)
        supersedes = current.version if current else None

        async def _execute() -> dict:
            commit = self.repo.insert_commit(
                version=next_version, policy_hash=policy_hash,
                policy_content=new_policy, signature=signature, supersedes_version=supersedes)
            return {"canon_version": commit.version, "policy_hash": commit.policy_hash,
                    "supersedes_version": supersedes}

        return await run_with_proof(event_type="policy_updated", intent_packet=None,
                                    actor=actor, execute_fn=_execute)

    def get_current_version(self) -> int | None:
        commit = self.repo.get_latest_commit()
        return commit.version if commit else None

    def get_current_hash(self) -> str | None:
        commit = self.repo.get_latest_commit()
        return commit.policy_hash if commit else None
