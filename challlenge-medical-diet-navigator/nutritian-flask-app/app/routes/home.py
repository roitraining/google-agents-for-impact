# app/routes/home.py
from __future__ import annotations
from flask import Blueprint, render_template, request, jsonify, session as flask_session, current_app
import os, asyncio, uuid, logging, threading
from mimetypes import guess_type
from config import Config
from google.cloud import storage

logging.basicConfig(level=logging.INFO)
home_bp = Blueprint("home", __name__)

RE_FULL = Config.Agent_Engine_Full_Adress
PROJECT_ID = Config.PROJECT_ID
LOCATION = Config.LOCATION
UPLOAD_BUCKET = Config.UPLOAD_BUCKET # <-- set this

_adk_app = None
_init_lock = threading.Lock()
def _get_adk_app():
    """
    Lazily import agent_engines, and cache the Agent Engine handle.
    Safe to be called from multiple threads.
    """
    from vertexai import agent_engines
    global _adk_app
    with _init_lock:
        if _adk_app is not None:
            return _adk_app
        
        _adk_app = agent_engines.get(RE_FULL)
        return _adk_app

def _safe_event_text(ev) -> str:
    """Extract just the assistant-visible text from an Agent Engine event."""
    # Dict-shaped events (what you're getting)
    if isinstance(ev, dict):
        # Prefer final "output" if present
        out = ev.get("output")
        if isinstance(out, str) and out.strip():
            return out.strip()

        # Common shape: ev["content"]["parts"][i]["text"]
        content = ev.get("content") or {}
        parts = content.get("parts") or []
        texts = []
        for p in parts:
            if isinstance(p, dict):
                t = p.get("text")
                if isinstance(t, str) and t.strip():
                    texts.append(t.strip())
        if texts:
            return "\n".join(texts)

        # Fallbacks
        for k in ("text", "delta_text"):
            t = ev.get(k)
            if isinstance(t, str) and t.strip():
                return t.strip()
        return ""

    # SDK object fallback (has .content.parts[i].text)
    try:
        content = getattr(ev, "content", None)
        parts = getattr(content, "parts", None) if content is not None else None
        if parts:
            texts = []
            for p in parts:
                if hasattr(p, "text") and isinstance(p.text, str) and p.text.strip():
                    texts.append(p.text.strip())
            if texts:
                return "\n".join(texts)
    except Exception:
        pass

    # Nothing textual
    return ""

async def _ensure_session() -> tuple[str, str]:
    """
    Ensure we have a persistent (user_id, session_id) pair stored in the Flask session cookie.
    Creates a new Agent Engine session if missing.
    """
    adk_app = _get_adk_app()

    if "ae_user_id" not in flask_session:
        flask_session["ae_user_id"] = f"web-{uuid.uuid4().hex[:8]}"
    user_id = flask_session["ae_user_id"]

    # Create a new managed session if we don't already have one:
    if "ae_session_id" not in flask_session:
        sess = await adk_app.async_create_session(user_id=user_id)
        # The SDK returns a dict-like object; pull the ID field:
        session_id = sess.get("id") if isinstance(sess, dict) else getattr(sess, "id", None)
        if not session_id:
            raise RuntimeError("Failed to create Agent Engine session (no id returned).")
        flask_session["ae_session_id"] = session_id

    return user_id, flask_session["ae_session_id"]

@home_bp.route("/", methods=["GET"])
def home():
    flask_session.pop("ae_session_id", None)
    return render_template("home.html")


def _build_parts(prompt: str | None, file_uris: list[tuple[str, str]]):
    """
    Plain dict parts for Agent Engine. IMAGE FIRST, then text with a vision nudge.
    """
    parts = []
    # 1) Image(s) first
    for (uri, mime) in file_uris:
        parts.append({"file_data": {"mime_type": mime, "file_uri": uri}})
    # 2) Then the text
    if prompt:
        vision_nudge = (
            "You are vision-capable and an image is attached. "
            "Analyze the image and answer the question using what you see. "
            "Give ONE final answer (no intermediate messages)."
        )
        parts.append({"text": f"{vision_nudge}\n\n{prompt}"})
    return parts

def _build_message_content(prompt: str | None, file_uris: list[tuple[str, str]]):
    return {"role": "user", "parts": _build_parts(prompt, file_uris)}

def _extract_final_text(ev) -> str:
    # Prefer explicit final 'output' if present.
    if isinstance(ev, dict):
        out = ev.get("output")
        if isinstance(out, str) and out.strip():
            return out.strip()

        # If event has a 'stage'/'final' hint, only accept those.
        stage = ev.get("stage") or ev.get("status") or ""
        if stage in ("final", "completed", "done"):
            content = ev.get("content") or {}
            parts = content.get("parts") or []
            texts = [p.get("text","").strip() for p in parts if isinstance(p, dict) and p.get("text")]
            return "\n".join([t for t in texts if t]) or ""

    # Otherwise ignore (likely tool logs / interim deltas).
    return ""

import re

_IMG_BLIND_PAT = re.compile(
    r"\b(can'?t|cannot|unable to)\s+see\s+image(s)?\b", re.IGNORECASE
)

def _parse_event_text(ev) -> tuple[str | None, str | None]:
    """
    Return (final_text, delta_text)
      - final_text: a complete assistant message if this event carries one
      - delta_text: incremental text chunk (streaming delta), if present
    Handles dict-shaped events and SDK objects.
    """
    # Dict-shaped event
    if isinstance(ev, dict):
        # 1) explicit final 'output'
        out = ev.get("output")
        if isinstance(out, str) and out.strip():
            return out.strip(), None

        # 2) streaming delta
        d = ev.get("delta_text")
        if isinstance(d, str) and d:
            return None, d

        # 3) full assistant content in parts[]
        content = ev.get("content") or {}
        parts = content.get("parts") or []
        texts = []
        for p in parts:
            if isinstance(p, dict):
                t = p.get("text")
                if isinstance(t, str) and t.strip():
                    texts.append(t.strip())
        if texts:
            return "\n".join(texts), None

        # 4) legacy flat fields
        for k in ("text",):
            t = ev.get(k)
            if isinstance(t, str) and t.strip():
                return t.strip(), None

        return None, None

    # SDK object-shaped event
    try:
        out = getattr(ev, "output", None)
        if isinstance(out, str) and out.strip():
            return out.strip(), None

        d = getattr(ev, "delta_text", None)
        if isinstance(d, str) and d:
            return None, d

        content = getattr(ev, "content", None)
        parts = getattr(content, "parts", None) if content is not None else None
        if parts:
            texts = []
            for p in parts:
                t = getattr(p, "text", None)
                if isinstance(t, str) and t.strip():
                    texts.append(t.strip())
            if texts:
                return "\n".join(texts), None
    except Exception:
        pass

    return None, None



def _upload_to_gcs(image_bytes: bytes, mime_type: str) -> str:
    client = storage.Client()  # uses ADC
    bucket = client.bucket(UPLOAD_BUCKET)
    obj = f"chat-uploads/{uuid.uuid4().hex}"
    # (optional) add a sensible extension
    ext = {"image/png":"png","image/jpeg":"jpg","image/webp":"webp"}.get(mime_type, "bin")
    blob = bucket.blob(f"{obj}.{ext}")
    blob.upload_from_string(image_bytes, content_type=mime_type)
    return f"gs://{bucket.name}/{blob.name}"

# async def _ask_agent_mm(prompt: str, image_bytes: bytes | None = None, mime_type: str | None = None) -> str:
#     user_id, session_id = await _ensure_session()
#     adk_app = _get_adk_app()

#     file_uris: list[tuple[str, str]] = []
#     if image_bytes and mime_type and mime_type.startswith("image/"):
#         gcs_uri = _upload_to_gcs(image_bytes, mime_type)
#         file_uris.append((gcs_uri, mime_type))

#     # Build the message in the format this Engine version accepts
#     if file_uris:
#         message = _build_message_content(prompt, file_uris)   # dict: {"role":"user","parts":[...]}
#     else:
#         message = prompt or " "                                # text-only as string

#     chunks = []
#     async for event in adk_app.async_stream_query(
#         user_id=user_id,
#         session_id=session_id,
#         message=message,            # <-- message ONLY; no 'content='
#     ):
#         #txt = _safe_event_text(event)
#         txt = _extract_final_text(event)
#         if txt:
#             chunks.append(txt)

#     return ("\n".join(chunks)).strip()

async def _ask_agent_mm(prompt: str, image_bytes: bytes | None = None, mime_type: str | None = None) -> str:
    user_id, session_id = await _ensure_session()
    adk_app = _get_adk_app()

    file_uris: list[tuple[str, str]] = []
    if image_bytes and mime_type and mime_type.startswith("image/"):
        gcs_uri = _upload_to_gcs(image_bytes, mime_type)
        file_uris.append((gcs_uri, mime_type))

    # Build message: image FIRST, then text with a gentle vision hint
    if file_uris:
        parts = []
        for (uri, m) in file_uris:
            parts.append({"file_data": {"mime_type": m, "file_uri": uri}})
        if prompt:
            parts.append({
                "text": (
                    "You are vision-capable and an image is attached. "
                    "Analyze the image and answer the question using what you see. "
                    "Return ONE final answer."
                    "\n\n" + prompt
                )
            })
        message = {"role": "user", "parts": parts}
    else:
        message = prompt or " "

    # Stream + aggregate
    delta_buf: list[str] = []
    last_complete: str | None = None
    have_image = bool(file_uris)

    async for event in adk_app.async_stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message,     # <-- your Engine requires 'message'
    ):
        final_text, delta_text = _parse_event_text(event)

        # collect deltas (useful when only delta_text arrives)
        if isinstance(delta_text, str) and delta_text:
            delta_buf.append(delta_text)

        # accept complete messages; prefer the latest
        if isinstance(final_text, str) and final_text.strip():
            # If an image was included, drop obvious “I can’t see images” intermediates
            if have_image and _IMG_BLIND_PAT.search(final_text):
                continue
            last_complete = final_text.strip()

    # Pick best available
    if last_complete:
        return last_complete
    if delta_buf:
        joined = "".join(delta_buf).strip()
        if have_image and _IMG_BLIND_PAT.search(joined):
            # guard against only getting the blind message in deltas
            return "Sorry—I couldn’t extract a final answer. Try a smaller/clearer image or add ingredients."
        return joined
    return "Sorry—I didn’t receive any text back from the agent."


@home_bp.route("/chat", methods=["POST"])
def chat():
    # Accept JSON or multipart/form-data
    image_bytes = None
    mime_type = None
    prompt = ""

    if request.content_type and "multipart/form-data" in request.content_type:
        prompt = (request.form.get("prompt") or "").strip()
        file = request.files.get("image")
        if file and file.filename:
            image_bytes = file.read()
            mime_type = file.mimetype or guess_type(file.filename)[0] or "application/octet-stream"
    else:
        data = request.get_json(silent=True) or {}
        prompt = (data.get("prompt") or "").strip()

    if not prompt and not image_bytes:
        return jsonify({"error": "Please provide a prompt or an image."}), 400

    try:
        reply = asyncio.run(_ask_agent_mm(prompt, image_bytes, mime_type))
        return jsonify({"reply": reply})
    except Exception as e:
        logging.exception("Chat error")
        return jsonify({"error": str(e)}), 500
