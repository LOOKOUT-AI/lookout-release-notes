"""HubSpot CRM contact adapter (CRM v3 objects API).

Auth: a Private App access token with ``crm.objects.contacts.read`` and
``crm.objects.contacts.write`` scopes. Pass it as HUBSPOT_TOKEN.
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from ..models import Contact, ContactRecord
from .base import Provider

_BASE = "https://api.hubapi.com/crm/v3/objects/contacts"
_PROPS = ["firstname", "lastname", "email", "phone", "company", "jobtitle", "hs_linkedin_url"]


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class HubSpotProvider(Provider):
    name = "hubspot"

    def __init__(self, token: str, timeout: int = 30) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        self._timeout = timeout

    def _to_contact(self, props: dict) -> Contact:
        return Contact(
            first_name=props.get("firstname") or "",
            last_name=props.get("lastname") or "",
            company=props.get("company") or "",
            title=props.get("jobtitle") or "",
            linkedin_url=props.get("hs_linkedin_url") or "",
            emails=[props["email"]] if props.get("email") else [],
            phones=[props["phone"]] if props.get("phone") else [],
        )

    def _to_props(self, contact: Contact) -> dict:
        props = {
            "firstname": contact.first_name,
            "lastname": contact.last_name,
            "company": contact.company,
            "jobtitle": contact.title,
            "hs_linkedin_url": contact.linkedin_url,
        }
        if contact.primary_email:
            props["email"] = contact.primary_email
        if contact.phones:
            props["phone"] = contact.phones[0]
        # HubSpot rejects empty-string writes for some props; send only filled.
        return {k: v for k, v in props.items() if v}

    def fetch(self) -> list[ContactRecord]:
        records: list[ContactRecord] = []
        after: str | None = None
        while True:
            params = {"limit": 100, "properties": ",".join(_PROPS)}
            if after:
                params["after"] = after
            resp = self._session.get(_BASE, params=params, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
            for obj in data.get("results", []):
                props = obj.get("properties", {})
                records.append(
                    ContactRecord(
                        provider=self.name,
                        record_id=str(obj["id"]),
                        contact=self._to_contact(props),
                        updated_at=_parse_ts(obj.get("updatedAt")),
                    )
                )
            after = data.get("paging", {}).get("next", {}).get("after")
            if not after:
                break
        return records

    def create(self, contact: Contact) -> str:
        resp = self._session.post(
            _BASE, json={"properties": self._to_props(contact)}, timeout=self._timeout
        )
        resp.raise_for_status()
        return str(resp.json()["id"])

    def update(self, record_id: str, contact: Contact) -> None:
        resp = self._session.patch(
            f"{_BASE}/{record_id}",
            json={"properties": self._to_props(contact)},
            timeout=self._timeout,
        )
        resp.raise_for_status()
