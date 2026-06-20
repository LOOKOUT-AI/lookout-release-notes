"""Two-way sync engine.

Algorithm per run:

1. Fetch every contact from every provider.
2. Cluster records into people (shared email + prior links).
3. For each person, decide the canonical contact:
   - Records whose content changed since last sync are the "edits".
   - Merge edits field-by-field, applied oldest-first so the most recent edit
     wins (last-write-wins conflict resolution). The most complete current
     record seeds the merge so untouched fields are preserved.
4. Write the canonical contact back to every provider that is missing it or
   out of date (create or update). ``dry_run`` reports the plan without writing.
5. Record new hashes/links in the state store.

The result is convergent: running twice with no external edits is a no-op.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .matching import cluster_records
from .models import Contact, ContactRecord
from .providers.base import Provider
from .state import StateStore


@dataclass
class PlannedChange:
    provider: str
    action: str  # "create" | "update"
    record_id: str | None
    contact: Contact


@dataclass
class SyncReport:
    people: int = 0
    in_sync: int = 0
    changes: list[PlannedChange] = field(default_factory=list)
    duplicates: list[tuple[str, str]] = field(default_factory=list)
    dry_run: bool = False

    def summary(self) -> str:
        creates = sum(1 for c in self.changes if c.action == "create")
        updates = sum(1 for c in self.changes if c.action == "update")
        mode = "DRY RUN — no writes" if self.dry_run else "applied"
        lines = [
            f"People: {self.people} ({self.in_sync} already in sync)",
            f"Planned: {creates} creates, {updates} updates ({mode})",
        ]
        if self.duplicates:
            lines.append(f"Duplicates flagged (same provider): {len(self.duplicates)}")
        return "\n".join(lines)


class SyncEngine:
    def __init__(self, providers: list[Provider], state: StateStore) -> None:
        if len(providers) < 2:
            raise ValueError("Need at least two providers to sync.")
        self.providers = providers
        self.state = state

    def _decide_canonical(
        self, records: list[ContactRecord]
    ) -> tuple[Contact, bool]:
        """Return ``(canonical_contact, changed)``."""
        edits: list[ContactRecord] = []
        for rec in records:
            prev = self.state.get(rec.provider, rec.record_id)
            if prev is None or prev.content_hash != rec.contact.content_hash():
                edits.append(rec)

        base = max(records, key=lambda r: r.contact.filled_count()).contact
        if not edits:
            return base, False

        merged = base.copy()
        for rec in sorted(edits, key=lambda r: r.updated_at_or_epoch()):
            merged = Contact.merge(merged, rec.contact)
        return merged, True

    def run(self, dry_run: bool = False) -> SyncReport:
        now = datetime.now(timezone.utc).isoformat()
        report = SyncReport(dry_run=dry_run)

        all_records: list[ContactRecord] = []
        for provider in self.providers:
            all_records.extend(provider.fetch())

        clusters = cluster_records(all_records, self.state.prior_links())
        report.people = len(clusters)

        by_name = {p.name: p for p in self.providers}

        for cluster in clusters:
            cluster_id = self._cluster_id(cluster)
            canonical, changed = self._decide_canonical(cluster)
            if not changed and len(cluster) == len(self.providers):
                report.in_sync += 1

            present: dict[str, list[ContactRecord]] = {}
            for rec in cluster:
                present.setdefault(rec.provider, []).append(rec)

            for provider in self.providers:
                recs = present.get(provider.name, [])
                if len(recs) > 1:
                    # Same person duplicated within one provider — flag, don't
                    # auto-delete. Sync against the most complete one.
                    recs.sort(key=lambda r: r.contact.filled_count(), reverse=True)
                    for dup in recs[1:]:
                        report.duplicates.append((provider.name, dup.record_id))

                if not recs:
                    change = PlannedChange(
                        provider.name, "create", None, canonical
                    )
                    report.changes.append(change)
                    if not dry_run:
                        new_id = by_name[provider.name].create(canonical)
                        self.state.upsert(
                            provider.name, new_id, cluster_id,
                            canonical.content_hash(), now,
                        )
                    continue

                rec = recs[0]
                if rec.contact.content_hash() != canonical.content_hash():
                    report.changes.append(
                        PlannedChange(
                            provider.name, "update", rec.record_id, canonical
                        )
                    )
                    if not dry_run:
                        by_name[provider.name].update(rec.record_id, canonical)

                if not dry_run:
                    self.state.upsert(
                        provider.name, rec.record_id, cluster_id,
                        canonical.content_hash(), now,
                    )

        return report

    def _cluster_id(self, cluster: list[ContactRecord]) -> str:
        """Reuse an existing cluster id if any record already has one, else mint
        a new stable id."""
        for rec in cluster:
            prev = self.state.get(rec.provider, rec.record_id)
            if prev is not None:
                return prev.cluster_id
        return uuid.uuid4().hex
