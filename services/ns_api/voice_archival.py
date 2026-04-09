from __future__ import annotations
import json
from run_with_proof import run_with_proof
from app.infra.repositories import VoiceSessionRepository, AlexandriaRepository

class VoiceSessionNotFound(Exception): pass
class VoiceSessionArchiveError(Exception): pass

async def close_voice_session(session_id: str, voice_repo: VoiceSessionRepository,
                               alexandria_repo: AlexandriaRepository) -> dict:
    session = voice_repo.get_voice_session(session_id)
    if session is None:
        raise VoiceSessionNotFound(f"session_id={session_id} not found")
    if not session.transcript:
        voice_repo.mark_voice_session_state(session_id, "error_no_transcript")
        raise VoiceSessionArchiveError(
            f"session_id={session_id}: cannot close — transcript empty. State=error_no_transcript.")

    async def _execute() -> dict:
        atom_id = alexandria_repo.insert_atom(type="voice_transcript",
                                               content=json.dumps(session.transcript),
                                               source_id=session.session_id)
        voice_repo.attach_memory_atom(session_id, atom_id)
        voice_repo.mark_voice_session_state(session_id, "complete")
        return {"session_id": session_id, "memory_atom_id": atom_id,
                "transcript_length": len(session.transcript), "state": "complete"}

    return await run_with_proof(event_type="voice_session_closed", intent_packet=None,
                                actor="voice_pipeline", execute_fn=_execute)
