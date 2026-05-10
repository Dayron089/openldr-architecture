#!/usr/bin/env python3
"""
LDR Admin CLI — обёртка над tools для вызова из OpenClaw exec.
Использование: python3 /app/ldr-tools/cli.py <tool_name> [json_args]

Примеры:
  python3 /app/ldr-tools/cli.py ldr_overview
  python3 /app/ldr-tools/cli.py ldr_revenue '{"period":"7d"}'
  python3 /app/ldr-tools/cli.py supabase_query '{"table":"users","limit":10}'
  python3 /app/ldr-tools/cli.py railway_logs '{"service":"backend","lines":30}'
"""

import sys
import os
import json
import asyncio
import time

import httpx

# --- Config ---

API_BASE = os.getenv("LDR_API_URL", "https://api.foreldr.com/api/v1")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

RAILWAY_API_TOKEN = os.getenv("RAILWAY_API_TOKEN", "")
RAILWAY_PROJECT_ID = os.getenv("RAILWAY_PROJECT_ID", "7c952838-c32f-4607-bb04-289d0eacb7be")
RAILWAY_SERVICES = {
    "backend": "5de80366-9737-4b03-bde4-ca6b1d43caf3",
    "bot": "386719ba-5ba2-4e0f-a808-e1d64e3e5272",
}
RAILWAY_ENVIRONMENT_ID = os.getenv("RAILWAY_ENVIRONMENT_ID", "15ae5dad-af56-499f-9045-4a9c002357c5")

ALLOWED_TABLES = {
    "users", "characters", "user_matches", "ldr_messages", "memories",
    "first_contacts", "user_character_relationships",
    "dialog_sessions", "session_messages",
    "schedules", "schedule_overrides", "scheduled_messages",
    "gift_catalog", "gift_purchases", "gift_achievements",
    "user_gift_achievements", "gift_streaks", "coin_transactions",
    "stories", "story_views", "story_schedule",
    "violations", "blocks", "gallery", "photo_jobs",
    "user_favorites", "admins", "admin_sessions", "admin_logs",
    "photo_reserves", "photo_reserve_transactions",
    "subscription_transactions",
}

# --- Auth ---

_token_cache = {"token": None, "expires_at": 0}


async def _get_token() -> str:
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 600:
        return _token_cache["token"]

    email = os.getenv("LDR_ADMIN_EMAIL", "")
    password = os.getenv("LDR_ADMIN_PASSWORD", "")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{API_BASE}/admin/login",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 14400)
    return _token_cache["token"]


async def _api_get(path: str, params: dict | None = None) -> str:
    token = await _get_token()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_BASE}/admin/api/{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        if resp.status_code == 401:
            _token_cache["token"] = None
            token = await _get_token()
            resp = await client.get(
                f"{API_BASE}/admin/api/{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
        resp.raise_for_status()
        return json.dumps(resp.json(), ensure_ascii=False, default=str)


def _supabase_headers() -> dict:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# --- Tool registry ---

TOOLS = {}


def tool(fn):
    TOOLS[fn.__name__] = fn
    return fn


# ==================== Admin API tools (20) ====================

@tool
async def ldr_overview(**kw): return await _api_get("overview")

@tool
async def ldr_live_pulse(**kw): return await _api_get("live-pulse")

@tool
async def ldr_system_health(**kw): return await _api_get("system-health")

@tool
async def ldr_business_alerts(**kw): return await _api_get("business-alerts")

@tool
async def ldr_revenue(period="", days=0, **kw):
    p = {}
    if period: p["period"] = period
    if days: p["days"] = days
    return await _api_get("revenue", p or None)

@tool
async def ldr_costs(period="", days=0, **kw):
    p = {}
    if period: p["period"] = period
    if days: p["days"] = days
    return await _api_get("costs", p or None)

@tool
async def ldr_analytics(period="", days=0, **kw):
    p = {}
    if period: p["period"] = period
    if days: p["days"] = days
    return await _api_get("analytics", p or None)

@tool
async def ldr_character_metrics(**kw): return await _api_get("character-metrics")

@tool
async def ldr_community_kpi(**kw): return await _api_get("community-kpi")

@tool
async def ldr_user_segments(**kw): return await _api_get("user-segments")

@tool
async def ldr_unit_economics(**kw): return await _api_get("unit-economics")

@tool
async def ldr_retention_cohorts(months=0, **kw):
    p = {}
    if months: p["months"] = months
    return await _api_get("retention-cohorts", p or None)

@tool
async def ldr_moderation_stats(**kw): return await _api_get("moderation-stats")

@tool
async def ldr_cron_health(**kw): return await _api_get("cron-health")

@tool
async def ldr_content_stats(**kw): return await _api_get("content-stats")

@tool
async def ldr_activity_feed(limit=0, **kw):
    p = {}
    if limit: p["limit"] = limit
    return await _api_get("activity-feed", p or None)

@tool
async def ldr_kpi_fast(**kw): return await _api_get("kpi-fast")

@tool
async def ldr_cost_analysis_sessions(period="", days=0, limit=0, **kw):
    p = {}
    if period: p["period"] = period
    if days: p["days"] = days
    if limit: p["limit"] = limit
    return await _api_get("cost-analysis/sessions", p or None)

@tool
async def ldr_timings(**kw): return await _api_get("timings")

@tool
async def ldr_command_center(**kw): return await _api_get("command-center")

@tool
async def ldr_financial_balances(**kw): return await _api_get("financial/balances")

@tool
async def ldr_financial_summary(**kw): return await _api_get("financial/summary")

@tool
async def ldr_trust_funnel(**kw): return await _api_get("trust-funnel")

@tool
async def ldr_subscription_analytics(**kw): return await _api_get("subscription-analytics")

@tool
async def ldr_costs_users(**kw): return await _api_get("costs/users")


# ==================== Railway Logs ====================

@tool
async def railway_logs(service="backend", lines=50, filter="", **kw):
    if not RAILWAY_API_TOKEN:
        return "RAILWAY_API_TOKEN not set"

    service_id = RAILWAY_SERVICES.get(service, RAILWAY_SERVICES["backend"])
    headers = {"Authorization": f"Bearer {RAILWAY_API_TOKEN}", "Content-Type": "application/json"}

    deploy_query = """
    query($serviceId: String!, $environmentId: String!) {
        deployments(input: {serviceId: $serviceId, environmentId: $environmentId}, first: 1) {
            edges { node { id status } }
        }
    }
    """
    log_query = """
    query($deploymentId: String!, $limit: Int, $filter: String) {
        deploymentLogs(deploymentId: $deploymentId, limit: $limit, filter: $filter) {
            timestamp message severity
        }
    }
    """

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post("https://backboard.railway.com/graphql/v2", headers=headers,
            json={"query": deploy_query, "variables": {"serviceId": service_id, "environmentId": RAILWAY_ENVIRONMENT_ID}})
        resp.raise_for_status()
        edges = resp.json().get("data", {}).get("deployments", {}).get("edges", [])
        if not edges:
            return "No active deployments"
        deployment_id = edges[0]["node"]["id"]

        variables = {"deploymentId": deployment_id, "limit": min(lines, 100)}
        if filter:
            variables["filter"] = filter
        resp2 = await client.post("https://backboard.railway.com/graphql/v2", headers=headers,
            json={"query": log_query, "variables": variables})
        resp2.raise_for_status()
        logs = resp2.json().get("data", {}).get("deploymentLogs", [])
        if not logs:
            return "Logs empty"

        result = []
        for entry in logs[-lines:]:
            ts = entry.get("timestamp", "")[:19]
            sev = entry.get("severity", "")
            msg = entry.get("message", "")
            prefix = f"[{sev}] " if sev and sev != "INFO" else ""
            result.append(f"{ts} {prefix}{msg}")
        return "\n".join(result)


# ==================== Story Monitor (4 tools) ====================

@tool
async def ldr_story_users(search="", subscription="", **kw):
    p = {}
    if search: p["search"] = search
    if subscription: p["subscription"] = subscription
    return await _api_get("story-monitor-v2/users", p or None)

@tool
async def ldr_story_characters(user_id="", **kw):
    return await _api_get(f"story-monitor-v2/users/{user_id}/characters")

@tool
async def ldr_story_details(character_id="", user_id="", **kw):
    return await _api_get(f"story-monitor-v2/characters/{character_id}/stories", {"user_id": user_id})

@tool
async def ldr_story_single(story_id="", **kw):
    return await _api_get(f"story-monitor-v2/stories/{story_id}")


# ==================== Supabase Tools (5 tools) ====================

@tool
async def supabase_query(table="", select="*", filters="", order="", limit=50, **kw):
    if table not in ALLOWED_TABLES:
        return f"Table '{table}' not in whitelist. Available: {', '.join(sorted(ALLOWED_TABLES))}"
    url = f"{SUPABASE_URL}/rest/v1/{table}?select={select}"
    if filters: url += f"&{filters}"
    if order: url += f"&order={order}"
    url += f"&limit={limit}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_supabase_headers())
        resp.raise_for_status()
        data = resp.json()
        return json.dumps(data, ensure_ascii=False, default=str) if data else f"{table}: 0 rows"

@tool
async def supabase_count(table="", filters="", **kw):
    if table not in ALLOWED_TABLES:
        return f"Table '{table}' not in whitelist"
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=count"
    if filters: url += f"&{filters}"
    h = _supabase_headers()
    h["Prefer"] = "count=exact"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.head(url, headers=h)
        resp.raise_for_status()
        count = resp.headers.get("content-range", "").split("/")[-1]
        return f"{table}: {count} rows"

@tool
async def supabase_delete(table="", filters="", **kw):
    if table not in ALLOWED_TABLES:
        return f"Table '{table}' not in whitelist"
    if not filters:
        return "REFUSED: DELETE without filters"
    url = f"{SUPABASE_URL}/rest/v1/{table}?{filters}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.delete(url, headers=_supabase_headers())
        resp.raise_for_status()
        result = resp.json() if resp.text else []
        return f"DELETE {table}: {len(result) if isinstance(result, list) else 1} rows"

@tool
async def supabase_update(table="", filters="", data="", **kw):
    if table not in ALLOWED_TABLES:
        return f"Table '{table}' not in whitelist"
    if not filters:
        return "REFUSED: UPDATE without filters"
    parsed = json.loads(data)
    url = f"{SUPABASE_URL}/rest/v1/{table}?{filters}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.patch(url, headers=_supabase_headers(), json=parsed)
        resp.raise_for_status()
        result = resp.json() if resp.text else []
        return f"UPDATE {table}: {len(result) if isinstance(result, list) else 1} rows"

@tool
async def supabase_insert(table="", data="", **kw):
    if table not in ALLOWED_TABLES:
        return f"Table '{table}' not in whitelist"
    parsed = json.loads(data)
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=_supabase_headers(), json=parsed)
        resp.raise_for_status()
        result = resp.json() if resp.text else []
        return f"INSERT {table}: {len(result) if isinstance(result, list) else 1} rows"


# ==================== Telegram Alert ====================

ALERT_STATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "workspace", "alert_state.json"
)
ALERT_STATE_FALLBACK = "/tmp/ldr_alert_state.json"


def _load_alert_state() -> dict:
    for path in (ALERT_STATE_PATH, ALERT_STATE_FALLBACK):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_alert_state(state: dict):
    import time
    cutoff = time.time() - 48 * 3600
    state = {k: v for k, v in state.items() if v > cutoff}
    for path in (ALERT_STATE_PATH, ALERT_STATE_FALLBACK):
        try:
            with open(path, "w") as f:
                json.dump(state, f)
            return
        except Exception:
            pass


@tool
async def ldr_alerts(**kw):
    """Активные алерты и статистика Alert Engine."""
    return await _api_get("alerts")


@tool
async def ldr_send_alert(message="", cooldown_hours=4, **kw):
    """Отправить алерт Диме. Дедупликация: повторный алерт с тем же текстом не отправляется
    раньше чем через cooldown_hours часов (default 4)."""
    import hashlib, time
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("ADMIN_USER_ID", "")
    if not message:
        return "ERROR: message is required"

    fingerprint = hashlib.sha256(message.strip().encode()).hexdigest()[:16]
    state = _load_alert_state()
    now = time.time()
    last_sent = state.get(fingerprint, 0)
    elapsed_h = (now - last_sent) / 3600

    if last_sent and elapsed_h < cooldown_hours:
        return f"SKIPPED: duplicate alert (last sent {elapsed_h:.1f}h ago, cooldown {cooldown_hours}h)"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        })
        resp.raise_for_status()

    state[fingerprint] = now
    _save_alert_state(state)
    return "Alert sent"


@tool
async def ldr_resolve_alert(message="", **kw):
    """Сбросить дедупликацию алерта — следующий ldr_send_alert с тем же текстом пройдёт.
    Вызывай когда проблема решена, чтобы разблокировать алерт."""
    import hashlib
    if not message:
        return "ERROR: message is required"
    fingerprint = hashlib.sha256(message.strip().encode()).hexdigest()[:16]
    state = _load_alert_state()
    if fingerprint in state:
        del state[fingerprint]
        _save_alert_state(state)
        return f"Alert resolved (fingerprint {fingerprint} cleared)"
    return f"Alert not found in state (fingerprint {fingerprint})"


# --- Main ---

async def main():
    if len(sys.argv) < 2:
        print(f"Available tools: {', '.join(sorted(TOOLS.keys()))}")
        sys.exit(0)

    tool_name = sys.argv[1]
    if tool_name not in TOOLS:
        print(f"Unknown tool: {tool_name}")
        print(f"Available: {', '.join(sorted(TOOLS.keys()))}")
        sys.exit(1)

    args = {}
    if len(sys.argv) > 2:
        args = json.loads(sys.argv[2])

    result = await TOOLS[tool_name](**args)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
