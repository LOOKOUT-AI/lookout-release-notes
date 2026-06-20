"""In-memory provider for testing the engine without network access."""

from __future__ import annotations

import itertools
from datetime import datetime, timezone

from contacts_sync.models import Contact, ContactRecord
from contacts_sync.providers.base import Provider


class FakeProvider(Provider):
    def __init__(self, name: str) -> None:
        self.name = name
        self.store: dict[str, ContactRecord] = {}
        self._ids = itertools.count(1)

    def seed(self, contact: Contact, when: datetime | None = None) -> str:
        rid = f"{self.name}-{next(self._ids)}"
        self.store[rid] = ContactRecord(
            provider=self.name, record_id=rid, contact=contact,
            updated_at=when or datetime.now(timezone.utc),
        )
        return rid

    def fetch(self) -> list[ContactRecord]:
        return [
            ContactRecord(r.provider, r.record_id, r.contact.copy(), r.updated_at)
            for r in self.store.values()
        ]

    def create(self, contact: Contact) -> str:
        rid = f"{self.name}-{next(self._ids)}"
        self.store[rid] = ContactRecord(
            self.name, rid, contact.copy(), datetime.now(timezone.utc)
        )
        return rid

    def update(self, record_id: str, contact: Contact) -> None:
        self.store[record_id].contact = contact.copy()
