"""Command-line entry point.

    python -m contacts_sync status        # what's configured + state stats
    python -m contacts_sync sync --dry-run  # plan, no writes
    python -m contacts_sync sync            # apply two-way sync
"""

from __future__ import annotations

import argparse
import sys

from .config import providers_from_env
from .engine import SyncEngine
from .state import StateStore

_DEFAULT_DB = "contacts_sync_state.db"


def _cmd_status(args: argparse.Namespace) -> int:
    providers = providers_from_env()
    print("Configured providers:", ", ".join(p.name for p in providers) or "(none)")
    with StateStore(args.db) as state:
        stats = state.stats()
    print(f"State: {stats['records']} records across {stats['people']} people")
    if len(providers) < 2:
        print("\nNeed at least two providers configured to sync. See .env.example.")
        return 1
    return 0


def _cmd_sync(args: argparse.Namespace) -> int:
    providers = providers_from_env()
    if len(providers) < 2:
        print("Need at least two providers configured. See .env.example.", file=sys.stderr)
        return 1
    with StateStore(args.db) as state:
        engine = SyncEngine(providers, state)
        report = engine.run(dry_run=args.dry_run)
    print(report.summary())
    if args.verbose:
        for c in report.changes:
            who = c.contact.full_name or (c.contact.primary_email or "?")
            print(f"  {c.action:6} {c.provider:8} {who}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contacts_sync")
    parser.add_argument("--db", default=_DEFAULT_DB, help="state DB path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="show configuration and state")
    p_status.set_defaults(func=_cmd_status)

    p_sync = sub.add_parser("sync", help="run a two-way sync")
    p_sync.add_argument("--dry-run", action="store_true", help="plan without writing")
    p_sync.add_argument("-v", "--verbose", action="store_true", help="list each change")
    p_sync.set_defaults(func=_cmd_sync)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
