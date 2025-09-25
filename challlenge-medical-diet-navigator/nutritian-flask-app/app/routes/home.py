# app/routes/home.py
from __future__ import annotations
from flask import Blueprint, render_template, request, jsonify, session as flask_session, current_app
import os, asyncio, uuid, logging


import vertexai
from vertexai import agent_engines

logging.basicConfig(level=logging.INFO)
home_bp = Blueprint("home", __name__)

RE_FULL = "projects/cool-benefit-472616-t9/locations/us-central1/reasoningEngines/6627156802838462464"
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "cool-benefit-472616-t9")
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)
adk_app = agent_engines.get(RE_FULL)  # Official pattern in docs

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


async def _ask_agent(prompt: str) -> str:
    """Stream a reply within the persistent Agent Engine session."""
    user_id, session_id = await _ensure_session()

    chunks = []
    async for event in adk_app.async_stream_query(
        user_id=user_id,
        session_id=session_id,            # <- critical for threaded memory
        message=prompt,
    ):
        txt = _safe_event_text(event)
        if txt:
            chunks.append(txt)

    reply = ("\n".join(chunks)).strip()
    return reply or "Sorry—I didn’t receive any text back from the agent."

@home_bp.route("/", methods=["GET"])
def home():
    flask_session.pop("ae_session_id", None)
    return render_template("home.html")

@home_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400
    try:
        # run the async streamer to completion
        reply = asyncio.run(_ask_agent(prompt))
        return jsonify({"reply": reply})
    except Exception as e:
        logging.exception("Chat error")
        return jsonify({"error": str(e)}), 500
