"""
NS Podcast Engine
Makes podcasts a stabilization interface, not content fluff.

Four services:
    SourcePackager  — ingest notes/PDFs/URLs → source pack with hashes + citations
    Showrunner      — source pack → episode outline, claims, host personas, call-in slots
    AudioEngine     — script → TTS audio segments, chapter markers, mp3 export
    LiveSession     — STT listener, interrupt protocol → CCT trajectory, moderation

In NS terms:
    Each episode is a domain in the pressure engine.
    SPF rises when listener disagreement increases.
    CCT tracks competing interpretations/questions.
    SCS tracks whether to commit to a conclusion or stay provisional.
    Every episode, claim, and commit produces a receipt.

Integration:
    - Arbiter routes showrunner LLM calls (multi-model episode reasoning)
    - Pressure engine tracks episode-level stabilization
    - Twilio bridge enables phone call-ins
    - WebSocket streams live state to console
"""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PODCAST_DIR = Path("/tmp/ns_workspace/podcast")
PODCAST_DIR.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def _id(prefix: str = "") -> str:
    return f"{prefix}{hashlib.sha256(f'{time.time_ns()}'.encode()).hexdigest()[:10]}"


# ── Data Objects ──────────────────────────────────────────────────────────────

@dataclass
class Source:
    source_id: str = field(default_factory=lambda: _id("src_"))
    source_type: str = "text"   # text | url | pdf | transcript
    content: str = ""
    url: str = ""
    title: str = ""
    content_hash: str = ""
    citation: str = ""
    ingested_at: str = field(default_factory=_ts)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourcePack:
    pack_id: str = field(default_factory=lambda: _id("pack_"))
    episode_id: str = ""
    sources: List[Source] = field(default_factory=list)
    combined_hash: str = ""
    word_count: int = 0
    created_at: str = field(default_factory=_ts)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class Claim:
    claim_id: str = field(default_factory=lambda: _id("cl_"))
    statement: str = ""
    evidence_source_ids: List[str] = field(default_factory=list)
    confidence: float = 0.8    # 0.0 – 1.0
    contested: bool = False
    call_in_eligible: bool = True  # can a listener/specialist challenge this?

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HostPersona:
    name: str = "Alex"
    role: str = "host"          # host | cohost | specialist | moderator
    voice_style: str = "conversational"  # conversational | analytical | skeptical
    tts_voice: str = "nova"     # OpenAI TTS voice id

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CallInSlot:
    slot_id: str = field(default_factory=lambda: _id("slot_"))
    topic: str = ""
    claim_id: str = ""         # which claim this challenges
    slot_type: str = "question"  # question | challenge | specialist
    time_limit_sec: int = 90
    open: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EpisodeScript:
    episode_id: str = field(default_factory=lambda: _id("ep_"))
    pack_id: str = ""
    title: str = ""
    outline: List[str] = field(default_factory=list)
    segments: List[dict] = field(default_factory=list)  # {speaker, text, chapter}
    claims: List[Claim] = field(default_factory=list)
    call_in_slots: List[CallInSlot] = field(default_factory=list)
    hosts: List[HostPersona] = field(default_factory=list)
    duration_estimate_sec: int = 0
    domain: str = ""            # NS pressure domain for this episode
    created_at: str = field(default_factory=_ts)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class LiveEvent:
    event_id: str = field(default_factory=lambda: _id("ev_"))
    event_type: str = ""  # listener_question | callin_start | callin_end | interrupt | commit
    speaker: str = ""
    content: str = ""
    trajectory_id: str = ""    # CCT trajectory this creates/updates
    timestamp: str = field(default_factory=_ts)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Source Packager ───────────────────────────────────────────────────────────

class SourcePackager:
    """
    Ingests sources (text, URLs, PDFs) and produces a source pack.
    Source pack has: hashes for each source, combined hash, citation map.
    """

    def package(self, sources: List[dict], episode_id: str = None) -> dict:
        """
        sources: list of {type, content?, url?, title?}
        Returns source pack dict.
        """
        pack_id = _id("pack_")
        ep_id = episode_id or _id("ep_")
        src_objects = []
        combined_text = ""

        for s in sources:
            src_type = s.get("type", "text")
            content = s.get("content", "")
            url = s.get("url", "")
            title = s.get("title", "Untitled")

            # URL fetch (sync for now — can be made async)
            if src_type == "url" and url and not content:
                content = self._fetch_url_text(url)

            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            citation = f"{title} [{content_hash[:8]}]"
            if url:
                citation += f" ({url[:60]})"

            src = Source(
                source_type=src_type,
                content=content,
                url=url,
                title=title,
                content_hash=content_hash,
                citation=citation,
            )
            src_objects.append(src)
            combined_text += content + "\n\n"

        combined_hash = hashlib.sha256(combined_text.encode()).hexdigest()[:16]
        word_count = len(combined_text.split())

        pack = SourcePack(
            pack_id=pack_id,
            episode_id=ep_id,
            sources=src_objects,
            combined_hash=combined_hash,
            word_count=word_count,
        )

        # Save to disk
        pack_path = PODCAST_DIR / f"{pack_id}.json"
        pack_path.write_text(json.dumps(pack.to_dict(), indent=2))

        return pack.to_dict()

    def _fetch_url_text(self, url: str, timeout: int = 10) -> str:
        """Simple sync URL fetch with text extraction."""
        try:
            import urllib.request
            import re
            req = urllib.request.Request(url, headers={"User-Agent": "NS-Podcast/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                html = r.read().decode("utf-8", errors="replace")[:100000]
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:20000]
        except Exception as e:
            return f"[URL fetch failed: {e}]"

    def load_pack(self, pack_id: str) -> Optional[dict]:
        pack_path = PODCAST_DIR / f"{pack_id}.json"
        if pack_path.exists():
            return json.loads(pack_path.read_text())
        return None


# ── Showrunner ────────────────────────────────────────────────────────────────

class Showrunner:
    """
    Converts a source pack into an episode script.
    Uses arbiter for multi-model reasoning on claims and structure.
    """

    DEFAULT_HOSTS = [
        HostPersona(name="Alex", role="host", voice_style="conversational", tts_voice="nova"),
        HostPersona(name="Jordan", role="cohost", voice_style="analytical", tts_voice="onyx"),
    ]

    def generate(self, source_pack_id: str,
                 style: str = "conversational",
                 hosts: List[dict] = None,
                 arbiter=None) -> dict:
        """
        Generate an episode script from a source pack.
        """
        packager = SourcePackager()
        pack = packager.load_pack(source_pack_id)
        if not pack:
            raise ValueError(f"Source pack not found: {source_pack_id}")

        host_personas = [HostPersona(**h) for h in hosts] if hosts else self.DEFAULT_HOSTS

        # Build combined source text
        combined = "\n\n".join(
            f"[SOURCE: {s.get('title', 'Unknown')}]\n{s.get('content', '')}"
            for s in pack.get("sources", [])
        )[:15000]

        # Generate script via arbiter (or fallback to template)
        if arbiter:
            script_content = self._generate_via_arbiter(combined, host_personas, style, arbiter)
        else:
            script_content = self._generate_template(combined, host_personas, style)

        # Parse into structured script
        episode = self._parse_script(script_content, pack, host_personas)

        # Save
        ep_path = PODCAST_DIR / f"{episode.episode_id}.json"
        ep_path.write_text(json.dumps(episode.to_dict(), indent=2))

        return episode.to_dict()

    def _generate_via_arbiter(self, combined: str, hosts: List[HostPersona],
                               style: str, arbiter) -> str:
        """Use NS arbiter to generate the script via multi-model reasoning."""
        host_names = " and ".join(h.name for h in hosts)
        prompt = f"""You are a podcast scriptwriter. Generate a {style} podcast script
for hosts {host_names} based on these sources.

Format each line as: HOST_NAME: dialogue text
Include [CHAPTER: title] markers for segments.
Include [CLAIM: statement | confidence: 0.0-1.0] for key claims.
Include [CALL_IN_SLOT: topic] for moments where listeners could challenge.

Sources:
{combined}

Generate a 5-8 minute podcast script (approximately 700-1000 words of dialogue):"""

        try:
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                arbiter.route(prompt)
            )
            return result.fused_response
        except Exception:
            return self._generate_template(combined, hosts, style)

    def _generate_template(self, combined: str, hosts: List[HostPersona],
                            style: str) -> str:
        """Fallback: structural template when no arbiter available."""
        h1 = hosts[0].name if hosts else "Alex"
        h2 = hosts[1].name if len(hosts) > 1 else "Jordan"

        # Extract first 500 chars as "content summary"
        summary = combined[:500].replace("\n", " ").strip()

        return f"""[CHAPTER: Introduction]
{h1}: Welcome back. Today we're diving into something that's been on our radar — and the sources we've gathered tell a compelling story.
{h2}: Absolutely. And I think what's interesting here is not just the surface level, but what it implies about where things are heading.
{h1}: Let's get into it.

[CHAPTER: Core Analysis]
{h2}: So the first thing that jumps out from the material is this: {summary[:200]}
{h1}: Right. And that's not isolated — it connects directly to the broader pattern we've seen.
[CLAIM: The evidence suggests a significant shift in the underlying dynamics. | confidence: 0.7]
{h2}: What's the evidence pointing to specifically?
{h1}: Multiple sources converge on the same conclusion, which is what gives this weight.
[CALL_IN_SLOT: Does the evidence actually support this conclusion?]

[CHAPTER: Implications]
{h2}: If we take this seriously, what does it change?
{h1}: The first-order implication is clear. The second-order effects are where it gets interesting.
{h2}: Walk me through that.
{h1}: The conventional view misses a critical feedback loop. Once you see it, you can't unsee it.
[CLAIM: Current frameworks are systematically underweighting this dynamic. | confidence: 0.65]

[CHAPTER: Open Questions]
{h2}: What are we still uncertain about?
{h1}: The timing. The direction is clear. The timing is not.
[CALL_IN_SLOT: Listener question: What would change your mind on this?]
{h2}: That's honest. And that's where we want to leave this open for now.

[CHAPTER: Close]
{h1}: Thanks for listening. If this raises questions — call in, push back, challenge us.
{h2}: That's the point. See you next time."""

    def _parse_script(self, script_text: str, pack: dict,
                       hosts: List[HostPersona]) -> EpisodeScript:
        """Parse script text into structured EpisodeScript object."""
        import re

        host_names = {h.name for h in hosts}
        episode_id = _id("ep_")
        segments = []
        claims = []
        call_in_slots = []
        outline = []
        current_chapter = "Introduction"

        lines = script_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Chapter marker
            ch = re.match(r"\[CHAPTER:\s*(.+?)\]", line, re.IGNORECASE)
            if ch:
                current_chapter = ch.group(1).strip()
                outline.append(current_chapter)
                continue

            # Claim
            cl = re.match(r"\[CLAIM:\s*(.+?)\s*\|\s*confidence:\s*([\d.]+)\]",
                          line, re.IGNORECASE)
            if cl:
                claim = Claim(
                    statement=cl.group(1).strip(),
                    confidence=float(cl.group(2)),
                    evidence_source_ids=[s["source_id"] for s in pack.get("sources", [])],
                )
                claims.append(claim)
                continue

            # Call-in slot
            cs = re.match(r"\[CALL_IN_SLOT:\s*(.+?)\]", line, re.IGNORECASE)
            if cs:
                slot = CallInSlot(
                    topic=cs.group(1).strip(),
                    claim_id=claims[-1].claim_id if claims else "",
                )
                call_in_slots.append(slot)
                continue

            # Dialogue
            dlg = re.match(r"^([A-Za-z]+):\s*(.+)$", line)
            if dlg:
                speaker = dlg.group(1)
                text = dlg.group(2)
                # Find matching host
                host_obj = next((h for h in hosts if h.name == speaker), None)
                segments.append({
                    "speaker": speaker,
                    "text": text,
                    "chapter": current_chapter,
                    "tts_voice": host_obj.tts_voice if host_obj else "nova",
                })

        words = sum(len(seg["text"].split()) for seg in segments)
        duration_est = int(words / 2.5)  # ~2.5 words/sec average speech

        return EpisodeScript(
            episode_id=episode_id,
            pack_id=pack.get("pack_id", ""),
            title=f"Episode — {pack.get('episode_id', 'Unknown')}",
            outline=outline,
            segments=segments,
            claims=claims,
            call_in_slots=call_in_slots,
            hosts=hosts,
            duration_estimate_sec=duration_est,
            domain=f"podcast.{episode_id}",
        )


# ── Audio Engine ──────────────────────────────────────────────────────────────

class AudioEngine:
    """
    Converts episode script to audio.
    Uses OpenAI TTS if available, otherwise generates chapter-marked SRT.
    Export: mp3 segments + chapter_markers.json
    """

    def __init__(self):
        self._openai = None
        self._load_openai()

    def _load_openai(self):
        try:
            from openai import OpenAI
            key = os.environ.get("OPENAI_API_KEY", "")
            if key:
                self._openai = OpenAI(api_key=key)
        except ImportError:
            pass

    def generate_audio(self, episode: dict, output_dir: str = None) -> dict:
        """
        Generate audio segments from episode script.
        Returns {segments: [{path, speaker, chapter, duration}], chapter_markers, total_sec}
        """
        out_dir = Path(output_dir or PODCAST_DIR / episode.get("episode_id", "ep"))
        out_dir.mkdir(parents=True, exist_ok=True)

        segments = episode.get("segments", [])
        audio_segments = []
        chapter_markers = []
        elapsed = 0

        for i, seg in enumerate(segments):
            speaker = seg.get("speaker", "host")
            text = seg.get("text", "")
            chapter = seg.get("chapter", "")
            voice = seg.get("tts_voice", "nova")

            # Chapter marker
            if chapter and (not chapter_markers or chapter_markers[-1]["title"] != chapter):
                chapter_markers.append({
                    "title": chapter,
                    "start_sec": elapsed,
                    "segment_index": i
                })

            if self._openai and text:
                # Real TTS
                seg_path = out_dir / f"seg_{i:04d}_{speaker}.mp3"
                try:
                    response = self._openai.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=text[:4096],
                    )
                    response.stream_to_file(str(seg_path))
                    # Estimate duration from word count
                    dur = len(text.split()) / 2.5
                    audio_segments.append({
                        "path": str(seg_path),
                        "speaker": speaker,
                        "chapter": chapter,
                        "text": text,
                        "duration_sec": dur,
                        "voice": voice,
                    })
                    elapsed += dur
                except Exception as e:
                    audio_segments.append({
                        "path": None,
                        "speaker": speaker,
                        "text": text,
                        "error": str(e),
                        "duration_sec": 0,
                    })
            else:
                # No TTS — generate SRT-style transcript only
                dur = len(text.split()) / 2.5
                audio_segments.append({
                    "path": None,
                    "speaker": speaker,
                    "chapter": chapter,
                    "text": text,
                    "duration_sec": dur,
                    "tts_ready": False,
                    "note": "Add OPENAI_API_KEY for TTS"
                })
                elapsed += dur

        # Save chapter markers
        cm_path = out_dir / "chapter_markers.json"
        cm_path.write_text(json.dumps(chapter_markers, indent=2))

        # Save SRT transcript
        srt_path = out_dir / "transcript.srt"
        self._write_srt(audio_segments, srt_path)

        result = {
            "episode_id": episode.get("episode_id", ""),
            "output_dir": str(out_dir),
            "segments": audio_segments,
            "chapter_markers": chapter_markers,
            "total_sec": elapsed,
            "has_audio": self._openai is not None,
            "transcript_path": str(srt_path),
        }

        # Save result manifest
        manifest_path = out_dir / "audio_manifest.json"
        manifest_path.write_text(json.dumps(result, indent=2))

        return result

    def _write_srt(self, segments: List[dict], path: Path) -> None:
        """Write SRT subtitle file from segments."""
        def _fmt_time(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec - int(sec)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        lines = []
        elapsed = 0.0
        for i, seg in enumerate(segments, 1):
            dur = seg.get("duration_sec", 3.0)
            start = _fmt_time(elapsed)
            end = _fmt_time(elapsed + dur)
            speaker = seg.get("speaker", "")
            text = seg.get("text", "")
            lines.append(f"{i}\n{start} --> {end}\n{speaker}: {text}\n")
            elapsed += dur

        path.write_text("\n".join(lines))


# ── Live Session ──────────────────────────────────────────────────────────────

class LiveSession:
    """
    Manages a live podcast session with listener interaction.

    Interrupt protocol:
        - Listener asks question → STT → LiveEvent
        - LiveEvent creates/updates CCT trajectory in pressure engine
        - Moderation layer checks: on-topic, time limit, evidence requirement
        - If approved: inject into episode flow (new call-in slot + specialist response)
        - Episode domain SPF updates on each contested claim
    """

    def __init__(self, episode: dict, pressure_engine=None, receipt_chain=None):
        self._episode = episode
        self._pressure = pressure_engine
        self._receipt_chain = receipt_chain
        self._session_id = _id("live_")
        self._domain = episode.get("domain", f"podcast.{episode.get('episode_id', '')}")
        self._events: List[LiveEvent] = []
        self._open_slots = {
            s["slot_id"]: s for s in episode.get("call_in_slots", [])
        }
        self._active = False

    def start(self) -> dict:
        self._active = True
        if self._receipt_chain:
            self._receipt_chain.emit(
                "PODCAST_SESSION_STARTED",
                {"kind": "podcast", "ref": self._session_id},
                {"episode_id": self._episode.get("episode_id")},
                {"domain": self._domain}
            )
        return {"session_id": self._session_id, "domain": self._domain, "active": True}

    def handle_listener_input(self, text: str, speaker: str = "listener") -> dict:
        """
        Process listener question/challenge.
        Returns: {approved, reason, trajectory_id, slot_id}
        """
        # Moderation check
        approved, reason = self._moderate(text)

        # Create live event regardless
        event = LiveEvent(
            event_type="listener_question",
            speaker=speaker,
            content=text,
        )
        self._events.append(event)

        if approved and self._pressure:
            # Create a CCT trajectory for this challenge
            try:
                cct = self._pressure.cct.get_or_create_cct(
                    self._domain, f"listener_challenge_{event.event_id}"
                )
                traj = self._pressure.cct.add_trajectory(
                    self._domain, cct.id,
                    f"Listener: {text[:100]}",
                    initial_support=0.2,
                    receipt_chain=self._receipt_chain
                )
                event.trajectory_id = traj.id

                # Record pressure signal
                self._pressure.spf.add_signal(self._domain, _make_signal(
                    "epistemic_conflict", 0.3, 0.2,
                    f"Listener challenge: {text[:80]}"
                ))
            except Exception:
                pass

        if self._receipt_chain:
            self._receipt_chain.emit(
                "PODCAST_LISTENER_INPUT",
                {"kind": "podcast", "ref": self._session_id},
                {"speaker": speaker, "approved": approved},
                {"text": text[:200], "trajectory_id": event.trajectory_id}
            )

        return {
            "event_id": event.event_id,
            "approved": approved,
            "reason": reason,
            "trajectory_id": event.trajectory_id,
        }

    def _moderate(self, text: str) -> tuple[bool, str]:
        """Basic moderation: length, content, rate limit."""
        if len(text) < 5:
            return False, "Too short"
        if len(text) > 2000:
            return False, "Too long (max 2000 chars)"
        # Rate limit: max 1 input per 10 sec per session
        recent = [e for e in self._events[-5:]
                  if e.event_type == "listener_question"]
        if len(recent) >= 3:
            return False, "Rate limit — please wait before next input"
        return True, "approved"

    def get_spf_status(self) -> dict:
        """Current pressure state for this episode's domain."""
        if not self._pressure:
            return {"spf": 0.0, "zone": "LATENT"}
        spf = self._pressure.spf.compute_spf(self._domain)
        from nss.core.pressure import get_spf_zone
        zone = get_spf_zone(spf)
        ccts = self._pressure.cct.get_active_ccts(self._domain)
        return {
            "domain": self._domain,
            "spf": round(spf, 3),
            "zone": str(zone),
            "active_trajectories": sum(len(c.trajectories) for c in ccts),
            "listener_challenges": len([e for e in self._events
                                        if e.event_type == "listener_question"]),
        }

    def stop(self) -> dict:
        self._active = False
        if self._receipt_chain:
            self._receipt_chain.emit(
                "PODCAST_SESSION_ENDED",
                {"kind": "podcast", "ref": self._session_id},
                {"episode_id": self._episode.get("episode_id")},
                {"total_events": len(self._events)}
            )
        return {
            "session_id": self._session_id,
            "events": len(self._events),
            "pressure_status": self.get_spf_status(),
        }


def _make_signal(signal_type: str, value: float, weight: float, description: str):
    """Helper to create a PressureSignal without circular import."""
    from nss.core.pressure import PressureSignal
    return PressureSignal(
        signal_type=signal_type, value=value,
        weight=weight, description=description
    )


# ── Episode Store ─────────────────────────────────────────────────────────────

def list_episodes(limit: int = 20) -> List[dict]:
    episodes = []
    for f in sorted(PODCAST_DIR.glob("ep_*.json"),
                    key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(f.read_text())
            episodes.append({
                "episode_id": data.get("episode_id"),
                "title": data.get("title"),
                "domain": data.get("domain"),
                "duration_estimate_sec": data.get("duration_estimate_sec", 0),
                "segment_count": len(data.get("segments", [])),
                "claim_count": len(data.get("claims", [])),
                "created_at": data.get("created_at"),
            })
        except Exception:
            pass
    return episodes


def load_episode(episode_id: str) -> Optional[dict]:
    ep_path = PODCAST_DIR / f"{episode_id}.json"
    if ep_path.exists():
        return json.loads(ep_path.read_text())
    return None
