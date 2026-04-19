"""axiolev-media-init-v2-stub — Media engine absent; stub package only."""
def pgvector_available() -> bool:
    return False
def build_skip_reason():
    return {"status": "skipped", "reason": "media_engine_repo.zip not provided",
            "advisory": "upload media_engine_repo.zip to uploads dir and re-run"}
def mount(*args, **kwargs) -> bool:
    return False
