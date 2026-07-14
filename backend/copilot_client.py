"""
copilot_client.py — Microsoft Copilot Studio Direct Line Client
=================================================================
Communicates with the Copilot Studio agent via the Direct Line API (v3).

Flow per user turn:
  1. Start/continue a conversation (POST /conversations)
  2. Send user message as an activity (POST /conversations/{id}/activities)
  3. Poll for the bot's reply activity
  4. Return the bot's text response

Prerequisites:
  - Copilot Studio agent published with Direct Line channel enabled
  - DIRECTLINE_SECRET environment variable set

Reference: https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-direct-line-3-0-concepts
"""

import os
import asyncio
import httpx

# ---------- Configuration ----------
DIRECTLINE_SECRET = os.getenv("DIRECTLINE_SECRET", "")
DIRECTLINE_BASE = "https://directline.botframework.com/v3/directline"

# Polling settings for bot response
POLL_INTERVAL_SEC = 0.5     # Time between polls
POLL_TIMEOUT_SEC = 30       # Max wait time for a response


class CopilotClient:
    """Async client for Microsoft Copilot Studio via Direct Line API."""

    def __init__(self):
        self._http = httpx.AsyncClient(timeout=30)
        # Cache active conversations for memory/context continuity
        # Format: { session_id: { "conversation_id": str, "token": str, "watermark": str } }
        self._sessions: dict = {}

    async def send_message(self, text: str, session_id: str = "default") -> str:
        """
        Send a text message to the Copilot agent and return its response.
        Uses session_id to maintain conversation memory across turns.
        """
        if not DIRECTLINE_SECRET:
            return self._fallback_response(text)

        # Start new conversation or reuse existing one
        session = self._sessions.get(session_id)
        if not session:
            session = await self._start_conversation()
            self._sessions[session_id] = session

        conv_id = session["conversation_id"]
        token = session["token"]
        watermark = session.get("watermark")

        # Send user message as a Direct Line activity
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        activity = {
            "type": "message",
            "from": {"id": f"user-{session_id}"},
            "text": text,
        }
        await self._http.post(f"{DIRECTLINE_BASE}/conversations/{conv_id}/activities", json=activity, headers=headers)

        # Poll for bot response — pass session_id so watermark updates the right session
        response_text = await self._poll_response(conv_id, token, watermark, session_id)
        return response_text

    async def _start_conversation(self) -> dict:
        """Start a new Direct Line conversation. Returns session dict."""
        headers = {"Authorization": f"Bearer {DIRECTLINE_SECRET}"}
        resp = await self._http.post(f"{DIRECTLINE_BASE}/conversations", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return {
            "conversation_id": data["conversationId"],
            "token": data.get("token", DIRECTLINE_SECRET),
            "watermark": None,
        }

    async def _poll_response(self, conv_id: str, token: str, watermark: str = None, session_id: str = "default") -> str:
        """Poll for the bot's reply activity. Returns the response text."""
        headers = {"Authorization": f"Bearer {token}"}
        user_id = f"user-{session_id}"
        elapsed = 0

        while elapsed < POLL_TIMEOUT_SEC:
            await asyncio.sleep(POLL_INTERVAL_SEC)
            elapsed += POLL_INTERVAL_SEC

            url = f"{DIRECTLINE_BASE}/conversations/{conv_id}/activities"
            if watermark:
                url += f"?watermark={watermark}"

            resp = await self._http.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            for activity in data.get("activities", []):
                from_id = activity.get("from", {}).get("id", "")
                act_type = activity.get("type", "")

                if from_id == user_id:   # Skip our own sent message
                    continue

                print(f"[DEBUG] Bot activity: type={act_type}, from={from_id}, text={str(activity.get('text', ''))[:100]}")

                if act_type == "message":
                    text = activity.get("text", "")
                    if text.strip():
                        self._sessions[session_id]["watermark"] = data.get("watermark")
                        return text

        return "I'm sorry, the request timed out. Please try again."

    def _fallback_response(self, text: str) -> str:
        """
        Fallback when DIRECTLINE_SECRET is not configured.
        Returns a helpful message indicating Copilot Studio is not connected.
        Useful during development when agent isn't deployed yet.
        """
        return (
            f"[Copilot Studio not connected] Received your message: \"{text}\". "
            "To enable the AI agent, set the DIRECTLINE_SECRET environment variable "
            "with your Copilot Studio Direct Line secret. "
            "See the copilot_studio_guide.md for setup instructions."
        )

    async def close(self):
        """Cleanup HTTP client."""
        await self._http.aclose()


# Module-level singleton for use across the app
copilot = CopilotClient()
