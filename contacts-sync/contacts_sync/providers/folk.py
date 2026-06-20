"""Folk (folk.app) people adapter.

Auth: a Folk API key passed as FOLK_TOKEN (Bearer).

NOTE: Folk's public API surface has changed over time and the exact people
payload shape should be confirmed against the current docs at
https://developer.folk.app/. The field mapping below targets the documented
``people`` resource (firstName/lastName/emails/phones/jobTitle/company). If your
workspace returns a different shape, adjust ``_to_contact`` / ``_to_payload``
only — the rest of the engine is provider-agnostic.
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from ..models import Contact, ContactRecord
from .base import Provider

_BASE = "https://api.folk.app/v1/people"


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


class FolkProvider(Provider):
    name = "folk"

    def __init__(self, token: str, timeout: int = 30) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        self._timeout = timeout

    def _to_contact(self, obj: dict) -> Contact:
        emails = obj.get("emails") or []
        phones = obj.get("phones") or []
        # Folk sometimes nests as [{"value": "..."}]; accept both shapes.
        emails = [e["value"] if isinstance(e, dict) else e for e in emails]
        phones = [p["value"] if isinstance(p, dict) else p for p in phones]
        company = obj.get("company") or ""
        if isinstance(company, dict):
            company = company.get("name", "")
        return Contact(
            first_name=obj.get("firstName") or "",
            last_name=obj.get("lastName") or "",
            company=company,
            title=obj.get("jobTitle") or "",
            linkedin_url=obj.get("linkedinUrl") or "",
            emails=emails,
            phones=phones,
        )

    def _to_payload(self, contact: Contact) -> dict:
        payload = {
            "firstName": contact.first_name,
            "lastName": contact.last_name,
            "jobTitle": contact.title,
            "emails": contact.emails,
            "phones": contact.phones,
        }
        if contact.company:
            payload["company"] = contact.company
        if contact.linkedin_url:
            payload["linkedinUrl"] = contact.linkedin_url
        return {k: v for k, v in payload.items() if v not in ("", [], None)}

    def fetch(self) -> list[ContactRecord]:
        records: list[ContactRecord] = []
        cursor: str | None = None
        while True:
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            resp = self._session.get(_BASE, params=params, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data") or data.get("items") or []
            for obj in items:
                records.append(
                    ContactRecord(
                        provider=self.name,
                        record_id=str(obj["id"]),
                        contact=self._to_contact(obj),
                        updated_at=_parse_ts(obj.get("updatedAt") or obj.get("updated_at")),
                    )
                )
            cursor = (data.get("pagination") or {}).get("nextCursor")
            if not cursor:
                break
        return records

    def create(self, contact: Contact) -> str:
        resp = self._session.post(
            _BASE, json=self._to_payload(contact), timeout=self._timeout
        )
        resp.raise_for_status()
        body = resp.json()
        return str((body.get("data") or body)["id"])

    def update(self, record_id: str, contact: Contact) -> None:
        resp = self._session.patch(
            f"{_BASE}/{record_id}", json=self._to_payload(contact), timeout=self._timeout
        )
        resp.raise_for_status()
