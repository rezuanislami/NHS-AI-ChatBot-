"""Create JIRA Cloud issues from the support-ticket form.

The function calls the Atlassian REST API directly with `httpx` so we
avoid pulling in another dependency. Credentials and project settings
come from environment variables (see `app.config.settings`).

If JIRA is not configured locally, `create_jira_ticket` returns a
TicketResponse with `success=False` and a clear message so the
endpoint can return HTTP 503 without crashing - useful for marking,
demos, or developers without an Atlassian account.
"""

from __future__ import annotations

import base64
from typing import Any, Dict

import httpx

from app.config import settings
from app.schemas import TicketRequest, TicketResponse


# ----------------------------------------------------------------------
# Atlassian Document Format helper
# ----------------------------------------------------------------------

def _adf_paragraph(text: str) -> Dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}],
    }


def _build_description(payload: TicketRequest) -> Dict[str, Any]:
    """Build the JIRA description in Atlassian Document Format.

    Embeds the user-facing form fields (name, email, requested issue
    category, source, attachment filename) into the body so support
    staff get the full picture even if those fields don't map to JIRA
    custom fields.
    """
    blocks = [
        _adf_paragraph(payload.description),
        _adf_paragraph("---"),
        _adf_paragraph(f"Submitted by: {payload.name} <{payload.email}>"),
        _adf_paragraph(f"Requested category: {payload.issueType}"),
        _adf_paragraph(f"Priority requested: {payload.priority}"),
    ]
    if payload.source:
        blocks.append(_adf_paragraph(f"Source: {payload.source}"))
    if payload.attachment:
        blocks.append(
            _adf_paragraph(
                f"User indicated they have an attachment: "
                f"{payload.attachment.filename} "
                f"({payload.attachment.size} bytes, {payload.attachment.type})"
            )
        )

    return {"type": "doc", "version": 1, "content": blocks}


def _build_issue_payload(payload: TicketRequest) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
        "project": {"key": settings.JIRA_PROJECT_KEY},
        "summary": payload.subject[:255],
        "issuetype": {"name": settings.JIRA_DEFAULT_ISSUE_TYPE},
        "description": _build_description(payload),
        # Tag the requested category as a label so it is filterable in JIRA
        # without relying on a custom field that may not exist.
        "labels": [
            "nhs-careers-chatbot",
            _safe_label(payload.issueType),
        ],
    }

    # Priority is optional in many JIRA projects. Send it; if the server
    # rejects it we'll fall back to a no-priority retry.
    if payload.priority:
        fields["priority"] = {"name": payload.priority}

    return {"fields": fields}


def _safe_label(text: str) -> str:
    # JIRA labels can't contain spaces.
    cleaned = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.lower())
    cleaned = cleaned.strip("-")
    return cleaned or "uncategorised"


def _basic_auth_header() -> str:
    raw = f"{settings.JIRA_EMAIL}:{settings.JIRA_API_TOKEN}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------

async def create_jira_ticket(payload: TicketRequest) -> TicketResponse:
    if not settings.JIRA_CONFIGURED:
        return TicketResponse(
            success=False,
            message=(
                "JIRA is not configured on this server. Set JIRA_BASE_URL, "
                "JIRA_EMAIL, JIRA_API_TOKEN and JIRA_PROJECT_KEY in your .env "
                "file and restart the backend."
            ),
        )

    url = f"{settings.JIRA_BASE_URL}/rest/api/3/issue"
    headers = {
        "Authorization": _basic_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = _build_issue_payload(payload)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=body)

            # Some projects don't have a priority scheme - retry without it.
            if resp.status_code == 400 and "priority" in resp.text.lower():
                body["fields"].pop("priority", None)
                resp = await client.post(url, headers=headers, json=body)

        if resp.status_code in (200, 201):
            data = resp.json()
            key = data.get("key", "")
            return TicketResponse(
                success=True,
                ticketKey=key,
                url=f"{settings.JIRA_BASE_URL}/browse/{key}" if key else None,
                message="Ticket created successfully.",
            )

        # JIRA failure - bubble up a short error string.
        try:
            err_body = resp.json()
            err_text = (
                "; ".join(err_body.get("errorMessages", []))
                or "; ".join(f"{k}: {v}" for k, v in err_body.get("errors", {}).items())
                or resp.text
            )
        except Exception:
            err_text = resp.text or f"HTTP {resp.status_code}"

        return TicketResponse(
            success=False,
            message=f"JIRA rejected the request ({resp.status_code}): {err_text[:500]}",
        )

    except httpx.HTTPError as e:
        return TicketResponse(
            success=False,
            message=f"Could not reach JIRA: {e!r}",
        )
