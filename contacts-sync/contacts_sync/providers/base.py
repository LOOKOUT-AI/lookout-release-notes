"""Provider interface every adapter implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Contact, ContactRecord


class Provider(ABC):
    #: Stable short name, e.g. "hubspot", "folk", "apple".
    name: str

    @abstractmethod
    def fetch(self) -> list[ContactRecord]:
        """Return all contacts currently in this provider."""

    @abstractmethod
    def create(self, contact: Contact) -> str:
        """Create a contact; return the new native record id."""

    @abstractmethod
    def update(self, record_id: str, contact: Contact) -> None:
        """Update an existing contact in place."""
