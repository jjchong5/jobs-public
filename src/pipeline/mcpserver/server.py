"""Read-only MCP server exposing the jobs pipeline to external humans/agents.

Run: python -m pipeline.mcpserver.server
Env: MCP_SERVER_PORT (default 8420), PIPELINE_DB_REMOTE_PATH (optional, see
db_read.py), MCP_ALLOWED_HOSTS (comma-separated Host header allowlist for
the MCP SDK's built-in DNS-rebinding protection -- see below).

Exposes exactly three tools -- search_items, rank_items, export_top_n -- and
nothing else. No write tools exist in this process at all. Auth (bearer API
key) and rate limiting are enforced in ASGI middleware ahead of the MCP
app, so every tool call is covered uniformly regardless of which tool.
"""
import logging
import os

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

from pipeline.mcpserver import auth
from pipeline.mcpserver.schema import CallerWeights
from pipeline.mcpserver.tools import export_top_n as _export_top_n
from pipeline.mcpserver.tools import rank_items as _rank_items
from pipeline.mcpserver.tools import search_items as _search_items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP SDK's DNS-rebinding protection rejects any Host header not in this
# list (421 Misdirected Request) -- on by default, empty allowlist, so it
# silently blocks every request through a tunnel/reverse-proxy (ngrok, a
# real host's domain) unless that host is added explicitly. Keeping the
# protection ON and allowlisting known hosts (not disabling it) since it's
# a real defense against DNS rebinding against a server that also accepts
# localhost. MCP_ALLOWED_HOSTS lets the current tunnel/deploy domain be
# added without a code change each time it rotates.
_default_hosts = ["127.0.0.1", f"127.0.0.1:{os.getenv('MCP_SERVER_PORT', '8420')}",
                   "localhost", f"localhost:{os.getenv('MCP_SERVER_PORT', '8420')}"]
_extra_hosts = [h.strip() for h in os.getenv("MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]

mcp = FastMCP(
    name="jobs-pipeline",
    instructions=(
        "Read-only access to the author's personal job/event pipeline. Three tools: "
        "search_items (browse/filter), rank_items (sort by YOUR OWN weight "
        "preferences, not the author's), export_top_n (capped at 50 items). No "
        "write access, no full-DB export, no access to the author's personal "
        "ranking weights."
    ),
    transport_security=TransportSecuritySettings(
        allowed_hosts=_default_hosts + _extra_hosts,
        allowed_origins=["*"],  # Origin varies per external caller; Host allowlist above is the real guard
    ),
    stateless_http=True,
)


@mcp.tool()
def search_items(
    q: str | None = None,
    category: str | None = None,
    role_category: str | None = None,
    industry: str | None = None,
    seniority: str | None = None,
    engagement_type: str | None = None,
    company_stage: str | None = None,
    remote_type: str | None = None,
    source: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search/browse job & event items. All filters optional and combine
    with AND. `q` does a substring match on title/company. Returns up to
    `limit` items (server-capped at 200), newest posted_at first."""
    filters = {
        "q": q, "category": category, "role_category": role_category,
        "industry": industry, "seniority": seniority,
        "engagement_type": engagement_type, "company_stage": company_stage,
        "remote_type": remote_type, "source": source,
    }
    return _search_items(filters, limit=limit)


@mcp.tool()
def rank_items(
    weights: CallerWeights,
    q: str | None = None,
    category: str | None = None,
    role_category: str | None = None,
    industry: str | None = None,
    seniority: str | None = None,
    engagement_type: str | None = None,
    company_stage: str | None = None,
    remote_type: str | None = None,
    source: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Rank items by YOUR OWN preference weights (not the author's -- their personal
    weight tables are never exposed). Provide any subset of
    engagement_weights/seniority_weights/location_weights/sector_weights/
    stage_weights/role_category_weights/category_weights, each a dict of
    {value: multiplier} (baseline neutral is 1.0). Unset tables default to
    neutral. Returns items sorted by your resulting score, descending."""
    filters = {
        "q": q, "category": category, "role_category": role_category,
        "industry": industry, "seniority": seniority,
        "engagement_type": engagement_type, "company_stage": company_stage,
        "remote_type": remote_type, "source": source,
    }
    return _rank_items(filters, weights.as_profile_dict(), limit=limit)


@mcp.tool()
def export_top_n(
    weights: CallerWeights,
    n: int = 50,
    q: str | None = None,
    category: str | None = None,
    role_category: str | None = None,
    industry: str | None = None,
    seniority: str | None = None,
    engagement_type: str | None = None,
    company_stage: str | None = None,
    remote_type: str | None = None,
    source: str | None = None,
) -> list[dict]:
    """Download your top N items ranked by your own weights (see
    rank_items). Hard capped at 50 items regardless of requested `n` --
    there is no way to export the full dataset through this server. Also
    limited to 5 export calls/day per API key."""
    filters = {
        "q": q, "category": category, "role_category": role_category,
        "industry": industry, "seniority": seniority,
        "engagement_type": engagement_type, "company_stage": company_stage,
        "remote_type": remote_type, "source": source,
    }
    return _export_top_n(filters, weights.as_profile_dict(), n=n)


class AuthRateLimitMiddleware:
    """Plain ASGI middleware: validates the Authorization: Bearer <key>
    header against mcp_api_keys and enforces the per-key rate limit before
    any request reaches the MCP app. Applied ahead of the mounted MCP app
    so it covers every tool call uniformly -- no per-tool auth code needed.
    export_top_n's extra daily cap is still enforced separately inside
    tools.export_top_n's caller (auth.check_export_limit), since only that
    one tool needs it; this middleware only does the per-minute request cap
    + key validity that applies to everything.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        if request.url.path == "/health":
            await self.app(scope, receive, send)
            return

        header = request.headers.get("authorization", "")
        raw_key = header[7:] if header.lower().startswith("bearer ") else None

        conn = auth.get_keys_connection()
        try:
            ok, result = auth.validate_key(conn, raw_key)
        finally:
            conn.close()

        if not ok:
            response = JSONResponse({"error": result}, status_code=401)
            await response(scope, receive, send)
            return

        key_hash = result
        ok, msg = auth.check_rate_limit(key_hash)
        if not ok:
            response = JSONResponse({"error": msg}, status_code=429)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def build_app() -> Starlette:
    mcp_app = mcp.streamable_http_app()
    # Forward the sub-app's lifespan (it owns the StreamableHTTP session
    # manager's startup/shutdown) -- mounting without this silently drops
    # session-manager init and every tool call fails at runtime.
    app = Starlette(
        routes=[Route("/health", endpoint=health), Mount("/", app=mcp_app)],
        lifespan=mcp_app.router.lifespan_context,
    )
    app.add_middleware(AuthRateLimitMiddleware)
    return app


app = build_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_SERVER_PORT", "8420"))
    logger.info("Starting jobs-pipeline MCP server on 127.0.0.1:%d", port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
