"""Cluster contact records that refer to the same person across providers.

Clustering is by shared email (high precision). Prior links from the state
store are also honored so a person stays merged even if an email is later
removed from one side.
"""

from __future__ import annotations

from typing import Iterable

from .models import ContactRecord


class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self._parent.setdefault(x, x)
        root = x
        while self._parent[root] != root:
            root = self._parent[root]
        # path compression
        while self._parent[x] != root:
            self._parent[x], x = root, self._parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[ra] = rb


def _record_token(rec: ContactRecord) -> str:
    return f"rec:{rec.provider}:{rec.record_id}"


def cluster_records(
    records: Iterable[ContactRecord],
    prior_links: Iterable[tuple[str, str]] = (),
) -> list[list[ContactRecord]]:
    """Group records into clusters of the same person.

    ``prior_links`` is an iterable of ``(provider:record_id, cluster_id)`` pairs
    from a previous sync; records sharing a prior cluster_id are unioned even if
    they no longer share an email.
    """
    records = list(records)
    uf = _UnionFind()

    # Seed every record so singletons survive.
    for rec in records:
        uf.find(_record_token(rec))

    # Union by shared email key.
    by_key: dict[str, list[str]] = {}
    for rec in records:
        for key in rec.contact.match_keys():
            by_key.setdefault(key, []).append(_record_token(rec))
    for tokens in by_key.values():
        for other in tokens[1:]:
            uf.union(tokens[0], other)

    # Union by prior persisted cluster membership.
    by_cluster: dict[str, list[str]] = {}
    present = {_record_token(r) for r in records}
    for token, cluster_id in prior_links:
        if token in present:
            by_cluster.setdefault(cluster_id, []).append(token)
    for tokens in by_cluster.values():
        for other in tokens[1:]:
            uf.union(tokens[0], other)

    # Bucket records by their representative root.
    buckets: dict[str, list[ContactRecord]] = {}
    for rec in records:
        root = uf.find(_record_token(rec))
        buckets.setdefault(root, []).append(rec)
    return list(buckets.values())
