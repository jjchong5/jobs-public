# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: planning prompt for the 2026-07-02 overnight source-connection
#   pass ("prepare for another overnight run...") -- see
#   docs/ai_usage/prompt_log.md#src-pipeline-gmail_authpy
# Usage: Gmail API OAuth helper enabling the Handshake email-parsing source.
# -------------------------------------------------------------------------

"""Gmail API auth for the pipeline's own scheduled scrapers (Handshake/LinkedIn
email parsing). Separate from any Claude session's connected Gmail MCP tools --
this needs to work unattended, e.g. under Task Scheduler.

One-time setup: run `python -m pipeline.gmail_auth` interactively to do the
OAuth consent in a browser and write `token.json`. After that, `get_gmail_service()`
refreshes silently with no user interaction.
"""
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"


def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    get_gmail_service()
    print(f"OAuth consent complete. Token saved to {TOKEN_PATH}.")
