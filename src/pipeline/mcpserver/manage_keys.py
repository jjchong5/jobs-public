"""CLI for minting/revoking MCP server API keys.

Usage:
  python -m pipeline.mcpserver.manage_keys create --label "for-hackathon-agent"
  python -m pipeline.mcpserver.manage_keys list
  python -m pipeline.mcpserver.manage_keys revoke <id>
"""
import argparse
from datetime import datetime, timezone

from pipeline.mcpserver import auth


def create(label: str | None) -> None:
    raw_key = auth.generate_key()
    key_hash = auth.hash_key(raw_key)
    conn = auth.get_keys_connection()
    try:
        conn.execute(
            "INSERT INTO mcp_api_keys (key_hash, label, created_at) VALUES (?, ?, ?)",
            (key_hash, label, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    print("Key created. Store this now -- it is not recoverable (only the hash is stored):")
    print(raw_key)


def list_keys() -> None:
    conn = auth.get_keys_connection()
    try:
        rows = conn.execute(
            "SELECT id, label, created_at, revoked_at FROM mcp_api_keys ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        status = "revoked" if row["revoked_at"] else "active"
        print(f"{row['id']}\t{status}\t{row['label'] or ''}\t{row['created_at']}")


def revoke(key_id: int) -> None:
    conn = auth.get_keys_connection()
    try:
        conn.execute(
            "UPDATE mcp_api_keys SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
            (datetime.now(timezone.utc).isoformat(), key_id),
        )
        conn.commit()
        changed = conn.total_changes
    finally:
        conn.close()
    print(f"Revoked key {key_id}" if changed else f"Key {key_id} not found or already revoked")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create")
    p_create.add_argument("--label", default=None)

    sub.add_parser("list")

    p_revoke = sub.add_parser("revoke")
    p_revoke.add_argument("id", type=int)

    args = parser.parse_args()
    if args.cmd == "create":
        create(args.label)
    elif args.cmd == "list":
        list_keys()
    elif args.cmd == "revoke":
        revoke(args.id)


if __name__ == "__main__":
    main()
