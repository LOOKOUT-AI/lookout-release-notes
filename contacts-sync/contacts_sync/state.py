"""Persistent sync state (SQLite).

Tracks, per provider record: the cluster it belongs to and the content hash we
last wrote/saw. This is what lets the engine tell *what changed* since the last
run and keep identities linked across runs.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    provider     TEXT NOT NULL,
    record_id    TEXT NOT NULL,
    cluster_id   TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_synced  TEXT NOT NULL,
    PRIMARY KEY (provider, record_id)
);
CREATE INDEX IF NOT EXISTS idx_records_cluster ON records (cluster_id);
"""


@dataclass
class RecordState:
    provider: str
    record_id: str
    cluster_id: str
    content_hash: str


class StateStore:
    def __init__(self, path: str = "contacts_sync_state.db") -> None:
        self._conn = sqlite3.connect(path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "StateStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def get(self, provider: str, record_id: str) -> Optional[RecordState]:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT provider, record_id, cluster_id, content_hash "
                "FROM records WHERE provider = ? AND record_id = ?",
                (provider, record_id),
            )
            row = cur.fetchone()
        return RecordState(*row) if row else None

    def prior_links(self) -> list[tuple[str, str]]:
        """Return ``(token, cluster_id)`` pairs for matching.cluster_records."""
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT provider, record_id, cluster_id FROM records")
            return [
                (f"rec:{p}:{rid}", cid) for (p, rid, cid) in cur.fetchall()
            ]

    def upsert(
        self,
        provider: str,
        record_id: str,
        cluster_id: str,
        content_hash: str,
        last_synced: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO records (provider, record_id, cluster_id, content_hash, last_synced) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(provider, record_id) DO UPDATE SET "
            "cluster_id = excluded.cluster_id, "
            "content_hash = excluded.content_hash, "
            "last_synced = excluded.last_synced",
            (provider, record_id, cluster_id, content_hash, last_synced),
        )
        self._conn.commit()

    def stats(self) -> dict[str, int]:
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT COUNT(*) FROM records")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT cluster_id) FROM records")
            clusters = cur.fetchone()[0]
        return {"records": total, "people": clusters}
