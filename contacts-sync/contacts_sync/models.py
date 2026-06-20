"""Provider-agnostic contact model, normalization, and field-level merge.

This is the shared "lingua franca" every provider adapter translates to and
from. Keeping it small and normalized is what makes matching (dedup) and
conflict resolution tractable across Apple Contacts, HubSpot, and Folk.
"""

from __future__ import annotations

import dataclasses
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Optional

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Scalar fields use last-write-wins; list fields are unioned.
_SCALAR_FIELDS = ("first_name", "last_name", "company", "title", "linkedin_url")
_LIST_FIELDS = ("emails", "phones")


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_phone(value: str) -> str:
    """Reduce a phone number to a comparable form: a leading ``+`` (if any)
    followed by digits. Not full E.164 (no region inference) but stable enough
    to match the same number written different ways."""
    value = value.strip()
    plus = value.startswith("+")
    digits = re.sub(r"\D", "", value)
    return ("+" if plus else "") + digits


def _dedupe(values: Iterable[str]) -> list[str]:
    """Order-preserving dedupe; drops empties."""
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


@dataclass
class Contact:
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    title: str = ""
    linkedin_url: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        self.company = (self.company or "").strip()
        self.title = (self.title or "").strip()
        self.linkedin_url = (self.linkedin_url or "").strip()
        self.emails = _dedupe(normalize_email(e) for e in self.emails)
        self.phones = _dedupe(normalize_phone(p) for p in self.phones)

    @property
    def full_name(self) -> str:
        return " ".join(p for p in (self.first_name, self.last_name) if p)

    @property
    def primary_email(self) -> Optional[str]:
        return self.emails[0] if self.emails else None

    def match_keys(self) -> set[str]:
        """Identity keys used to cluster the same person across providers.

        Email is the only high-precision key, so it is the only one used for
        automatic clustering. (Name+company is intentionally *not* a match key
        — it produces false merges on common names.)
        """
        return {f"email:{e}" for e in self.emails}

    def filled_count(self) -> int:
        """How many fields carry data — used to pick the most complete record
        as a merge base."""
        n = sum(1 for f in _SCALAR_FIELDS if getattr(self, f))
        return n + len(self.emails) + len(self.phones)

    def content_hash(self) -> str:
        """Stable hash of normalized content, for change detection."""
        parts = [getattr(self, f) for f in _SCALAR_FIELDS]
        parts.append("|".join(sorted(self.emails)))
        parts.append("|".join(sorted(self.phones)))
        blob = "\x1f".join(parts)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def copy(self) -> "Contact":
        return dataclasses.replace(
            self, emails=list(self.emails), phones=list(self.phones)
        )

    @staticmethod
    def merge(base: "Contact", incoming: "Contact") -> "Contact":
        """Overlay ``incoming`` onto ``base``.

        Scalar fields: a non-empty value in ``incoming`` wins (last-write-wins
        at the call site — caller applies changes oldest-first so the most
        recent edit is applied last). List fields: union, with ``incoming``'s
        order taking precedence so its primary email/phone stays primary.
        """
        out = base.copy()
        for f in _SCALAR_FIELDS:
            v = getattr(incoming, f)
            if v:
                setattr(out, f, v)
        for f in _LIST_FIELDS:
            merged = _dedupe(list(getattr(incoming, f)) + list(getattr(out, f)))
            setattr(out, f, merged)
        return out


@dataclass
class ContactRecord:
    """A :class:`Contact` as it exists in one provider, with its native id and
    last-modified time (used for conflict resolution)."""

    provider: str
    record_id: str
    contact: Contact
    updated_at: Optional[datetime] = None

    def updated_at_or_epoch(self) -> datetime:
        return self.updated_at or EPOCH
