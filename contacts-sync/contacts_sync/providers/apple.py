"""Apple Contacts adapter via CardDAV (works with iCloud, cross-platform).

Auth: iCloud requires an **app-specific password** (Apple ID > Sign-In &
Security > App-Specific Passwords), not your normal password. Provide:

    APPLE_CARDDAV_URL   full address-book collection URL, e.g.
                        https://p<NN>-contacts.icloud.com/<dsid>/carddavhome/card/
    APPLE_USERNAME      your iCloud email
    APPLE_PASSWORD      the app-specific password

The collection URL is account-specific. Discover it once with a CardDAV client
or by a PROPFIND on https://contacts.icloud.com against your principal; this
adapter then talks directly to that collection.

Records are addressed by their resource href (used as ``record_id``). vCard 3.0
is produced/parsed with ``vobject``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import requests
import vobject

from ..models import Contact, ContactRecord
from .base import Provider

_PROPFIND_BODY = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<d:propfind xmlns:d="DAV:">'
    "<d:prop><d:getetag/><d:getlastmodified/><d:getcontenttype/></d:prop>"
    "</d:propfind>"
)
_DAV = "{DAV:}"


def _parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    from email.utils import parsedate_to_datetime

    try:
        dt = parsedate_to_datetime(value)
        return dt.astimezone(timezone.utc) if dt else None
    except (TypeError, ValueError):
        return None


class AppleContactsProvider(Provider):
    name = "apple"

    def __init__(self, base_url: str, username: str, password: str, timeout: int = 30) -> None:
        if not base_url.endswith("/"):
            base_url += "/"
        self._base = base_url
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._timeout = timeout

    # --- vCard <-> Contact -------------------------------------------------
    def _to_contact(self, card: "vobject.base.Component") -> Contact:
        first = last = company = title = linkedin = ""
        if hasattr(card, "n"):
            first = (card.n.value.given or "").strip()
            last = (card.n.value.family or "").strip()
        if hasattr(card, "org") and card.org.value:
            company = card.org.value[0] if isinstance(card.org.value, list) else str(card.org.value)
        if hasattr(card, "title"):
            title = card.title.value or ""
        emails = [e.value for e in card.contents.get("email", []) if e.value]
        phones = [t.value for t in card.contents.get("tel", []) if t.value]
        for url in card.contents.get("url", []):
            if url.value and "linkedin.com" in url.value.lower():
                linkedin = url.value
        return Contact(
            first_name=first, last_name=last, company=company,
            title=title, linkedin_url=linkedin, emails=emails, phones=phones,
        )

    def _to_vcard(self, contact: Contact, uid: str) -> str:
        card = vobject.vCard()
        card.add("uid").value = uid
        n = card.add("n")
        n.value = vobject.vcard.Name(family=contact.last_name, given=contact.first_name)
        card.add("fn").value = contact.full_name or (contact.primary_email or "Unknown")
        if contact.company:
            card.add("org").value = [contact.company]
        if contact.title:
            card.add("title").value = contact.title
        for i, email in enumerate(contact.emails):
            e = card.add("email")
            e.value = email
            e.type_param = "INTERNET" if i else "INTERNET,pref"
        for phone in contact.phones:
            card.add("tel").value = phone
        if contact.linkedin_url:
            card.add("url").value = contact.linkedin_url
        return card.serialize()

    # --- Provider API ------------------------------------------------------
    def fetch(self) -> list[ContactRecord]:
        resp = self._session.request(
            "PROPFIND", self._base,
            data=_PROPFIND_BODY,
            headers={"Depth": "1", "Content-Type": "application/xml"},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        tree = ET.fromstring(resp.content)

        records: list[ContactRecord] = []
        for response in tree.findall(f"{_DAV}response"):
            href_el = response.find(f"{_DAV}href")
            if href_el is None or not href_el.text or not href_el.text.endswith(".vcf"):
                continue
            href = href_el.text
            lastmod = None
            lm_el = response.find(f".//{_DAV}getlastmodified")
            if lm_el is not None:
                lastmod = _parse_http_date(lm_el.text)

            card_resp = self._session.get(self._abs(href), timeout=self._timeout)
            card_resp.raise_for_status()
            try:
                card = vobject.readOne(card_resp.text)
            except Exception:
                continue
            records.append(
                ContactRecord(
                    provider=self.name,
                    record_id=href,
                    contact=self._to_contact(card),
                    updated_at=lastmod,
                )
            )
        return records

    def create(self, contact: Contact) -> str:
        uid = uuid.uuid4().hex
        href = f"{self._base}{uid}.vcf"
        resp = self._session.put(
            href,
            data=self._to_vcard(contact, uid).encode("utf-8"),
            headers={"Content-Type": "text/vcard; charset=utf-8", "If-None-Match": "*"},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        # record_id is the path relative to the collection host.
        return href.replace(self._host(), "", 1)

    def update(self, record_id: str, contact: Contact) -> None:
        uid = record_id.rsplit("/", 1)[-1].removesuffix(".vcf")
        resp = self._session.put(
            self._abs(record_id),
            data=self._to_vcard(contact, uid).encode("utf-8"),
            headers={"Content-Type": "text/vcard; charset=utf-8"},
            timeout=self._timeout,
        )
        resp.raise_for_status()

    def _host(self) -> str:
        # scheme://host
        parts = self._base.split("/", 3)
        return "/".join(parts[:3])

    def _abs(self, href: str) -> str:
        if href.startswith("http"):
            return href
        return self._host() + href
