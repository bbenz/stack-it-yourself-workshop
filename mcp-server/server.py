"""An MCP server that knows the AGNTCon + MCPCon North America 2026 workshop schedule.

It runs as its own process in its own container, so every tool call crosses a process
boundary. With OpenTelemetry on, FastMCP reads the W3C trace context the agent puts in the
request's `_meta` field (MCP SEP-414) and continues the same trace.

The schedule is demo data, taken from the event's public workshop listing on
events.linuxfoundation.org (September 2026), with the summaries paraphrased.
To reuse this workshop for another event, replace the server `instructions` and `WORKSHOPS` below.
"""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP(
    "agntcon-schedule",
    instructions="Look up hands-on workshops at AGNTCon + MCPCon North America 2026 (San Jose, 22-23 October).",
)

WORKSHOPS = [  # event-specific demo data - replace for another event
    {
        "title": "Hands-on A2A: Service Discovery and Multi-Agent Delegation",
        "day": "2026-10-22", "weekday": "Thursday", "start": "10:35", "end": "12:10", "room": "LL21 DEF",
        "summary": "This 75-minute interactive workshop provides a hands-on environment for engineers to explore agent-to-agent (A2A) protocols through practical execution rather than product pitches.",
    },
    {
        "title": "The Buzz-Word Is Collaboration",
        "day": "2026-10-22", "weekday": "Thursday", "start": "14:20", "end": "15:55", "room": "LL21 DEF",
        "summary": "Put agents where the work is: a shared, channel-driven workspace where people and agents share conversations, code and reviews.",
    },
    {
        "title": "Keep Infrastructure Out of Your AI Agents and MCP Servers",
        "day": "2026-10-22", "weekday": "Thursday", "start": "16:05", "end": "17:40", "room": "LL21 DEF",
        "summary": "The agent gateway pattern: secure and federate MCP servers, route and fail over LLM traffic, enforce policy and observe agent traffic.",
    },
    {
        "title": "Break the Lethal Trifecta: Designing Access Boundaries Agents Can't Talk Their Way Past",
        "day": "2026-10-23", "weekday": "Friday", "start": "10:55", "end": "12:30", "room": "230A",
        "summary": "Bound a compromised agent's blast radius by design, using capability surfaces, gateway filtering and structural separation. Security.",
    },
    {
        "title": "Stack It Yourself: Open Infrastructure for AI Agents, from Compose to Cluster",
        "day": "2026-10-23", "weekday": "Friday", "start": "10:55", "end": "12:30", "room": "LL21 DEF",
        "summary": "Build an agent on open inference, trace it with OpenTelemetry and the LGTM stack, keep history in Redis, and move it from Compose to Kubernetes.",
    },
    {
        "title": "Governing AI Agent Actions: MCP and Beyond",
        "day": "2026-10-23", "weekday": "Friday", "start": "13:45", "end": "15:20", "room": "LL21 DEF",
        "summary": "Policy across MCP servers, CLIs, skills and generated code: managed registries, audit, shadow AI and token spend. Governance.",
    },
    {
        "title": "Secure Agentic Framework (SAF) for Agentic AI",
        "day": "2026-10-23", "weekday": "Friday", "start": "15:30", "end": "17:50", "room": "LL21 DEF",
        "summary": "Scan a vulnerable reference environment, map findings to SAF controls for MCP and Kubernetes, fix and re-scan. Security.",
    },
]


def _normalise_day(day: str) -> str | None:
    d = day.strip().lower()
    if any(k in d for k in ("22", "thu", "first", "day 1", "day one")):
        return "2026-10-22"
    if any(k in d for k in ("23", "fri", "second", "day 2", "day two", "last")):
        return "2026-10-23"
    return None


@mcp.tool
def list_workshops(day: str) -> list[dict]:
    """List the hands-on workshops on one conference day, in time order.

    Args:
        day: The conference day, e.g. "2026-10-22" (Thursday) or "2026-10-23" (Friday).
    """
    wanted = _normalise_day(day)
    if wanted is None:
        return [{"error": f"Unknown day {day!r}. The conference runs Thursday 2026-10-22 and Friday 2026-10-23."}]
    return sorted((w for w in WORKSHOPS if w["day"] == wanted), key=lambda w: w["start"])


@mcp.tool
def search_workshops(keyword: str) -> list[dict]:
    """Find workshops whose title or summary mentions a keyword, e.g. "security", "gateway", "MCP" or "Kubernetes".

    Args:
        keyword: A single word or short phrase to search for.
    """
    k = keyword.strip().lower()
    hits = [w for w in WORKSHOPS if k in w["title"].lower() or k in w["summary"].lower()]
    return hits or [{"result": f"No workshops mention {keyword!r}."}]


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.getenv("PORT", "8001")), show_banner=False)
