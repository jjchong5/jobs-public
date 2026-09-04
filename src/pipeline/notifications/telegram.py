# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "do we have notification built in? if not can we wire this to my telegram bot (see my other Telegram/Claude gateway project)" (2026-08-26)
# Usage: Minimal Telegram Bot API sendMessage wrapper, built from scratch. Reuses the
#   bot token already provisioned for a separate personal Telegram/Claude gateway
#   project rather than creating a new bot -- this project only needs one-way push,
#   not that other project's full conversational gateway.
# -------------------------------------------------------------------------

"""Thin wrapper around Telegram's Bot API sendMessage endpoint.

Reuses the bot token from a separate personal project (a self-hosted Telegram/
Claude gateway) rather than provisioning a second bot -- this
project only ever pushes one-way notifications, it doesn't need that other
project's full conversational/pairing machinery.

Requires two env vars (see .env.example):
  TELEGRAM_BOT_TOKEN -- same token as the other project's bot
  TELEGRAM_CHAT_ID   -- the numeric chat id to push into (get via
                        https://api.telegram.org/bot<token>/getUpdates after
                        sending the bot any message from the target chat)
"""
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


def send_telegram_message(text: str) -> bool:
    """Sends `text` to TELEGRAM_CHAT_ID via TELEGRAM_BOT_TOKEN. Returns True on
    success, False (logged, not raised) on any failure -- a notification
    failure should never take down the scrape/tag/rank run it's reporting on.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing) -- skipping notification")
        return False

    try:
        resp = requests.post(
            f"{TELEGRAM_API_BASE}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Telegram sendMessage failed")
        return False
