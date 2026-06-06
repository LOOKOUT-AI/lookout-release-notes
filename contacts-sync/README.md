# contacts-sync

Two-way contact synchronization across **Apple Contacts (iCloud)**, **HubSpot**,
and **Folk** — keeping the same person consistent and de-duplicated everywhere.

> Status: working core engine with passing tests. Live provider adapters are
> implemented but need real credentials to validate end-to-end. See
> [Status & next steps](#status--next-steps).

## How it works

Each provider is translated to a shared, normalized `Contact` model, so matching
and conflict resolution don't care which system a record came from.

```
Apple ─┐
HubSpot├─► fetch ─► cluster (by email) ─► decide canonical (last-write-wins)
Folk  ─┘                                       │
                                               └─► write back to every provider
                                                   that's missing/out-of-date
```

1. **Fetch** every contact from every configured provider.
2. **Cluster** records that are the same person — by shared email (high
   precision), plus prior links remembered in the state DB so people stay merged
   even if an email later changes.
3. **Decide the canonical version**: records changed since the last sync are
   merged field-by-field, applied oldest→newest so the **most recent edit wins**.
   Untouched fields are preserved from the most complete record. List fields
   (emails, phones) are **unioned**, not overwritten.
4. **Write back** — create where missing, update where stale, on every provider.
5. **Persist** content hashes + cluster links so the next run knows what changed.

The sync is **convergent**: running it twice with no external edits does nothing.
`--dry-run` prints the plan without writing.

## Layout

```
contacts_sync/
  models.py          normalized Contact, normalization, field-level merge
  matching.py        cluster records into people (union-find over emails)
  state.py           SQLite state store (cluster links + content hashes)
  engine.py          two-way sync orchestration + conflict resolution
  config.py          build providers from env vars
  cli.py             status / sync commands
  providers/
    base.py          Provider interface (fetch / create / update)
    hubspot.py       HubSpot CRM v3
    folk.py          Folk people API
    apple.py         Apple Contacts via iCloud CardDAV (vobject)
tests/               pure-logic + full round-trip tests (in-memory provider)
```

## Setup

```bash
cd contacts-sync
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in credentials
```

Credentials (set only the ones you want active — two providers minimum):

| Var | Where to get it |
| --- | --- |
| `HUBSPOT_TOKEN` | HubSpot → Settings → Integrations → **Private Apps**, scopes `crm.objects.contacts.read` + `.write` |
| `FOLK_TOKEN` | Folk API key — https://developer.folk.app/ |
| `APPLE_CARDDAV_URL`, `APPLE_USERNAME`, `APPLE_PASSWORD` | iCloud CardDAV collection URL + Apple ID + an **app-specific password** |

## Usage

```bash
set -a; . .env; set +a            # load credentials

python -m contacts_sync status            # what's configured + state stats
python -m contacts_sync sync --dry-run -v # show the plan, write nothing
python -m contacts_sync sync              # apply the two-way sync
```

Run on a schedule (cron/launchd) for continuous sync. The state DB
(`contacts_sync_state.db`) must persist between runs.

## Tests

```bash
. .venv/bin/activate
pip install pytest
python -m pytest -q      # 13 passing: models, matching, full sync round-trip
```

The engine tests use an in-memory `FakeProvider`, so they exercise the real
clustering / merge / convergence logic without any network or credentials.

## Conflict resolution

- **Scalar fields** (name, company, title, LinkedIn): last-write-wins by the
  source record's `updatedAt`.
- **List fields** (emails, phones): unioned — nothing is lost.
- **Duplicates within one provider**: flagged in the report, never auto-deleted.
  Sync proceeds against the most complete record.

## Status & next steps

**Done and verified**
- Normalized model, email-based identity matching, field-level LWW merge,
  union of multi-valued fields, convergent two-way engine, SQLite state,
  CLI (`status` / `sync` / `--dry-run`) — all covered by passing tests.

**Implemented, needs live validation with real credentials**
- HubSpot adapter (pagination, create/update).
- Folk adapter — confirm the people payload shape against your workspace's
  current API response; mapping is isolated to `_to_contact`/`_to_payload`.
- Apple/iCloud CardDAV adapter — the collection URL is account-specific and
  must be discovered once.

**Not yet implemented (intentional, call before adding)**
- Deletions/archival propagation (current engine creates/updates only — safe by
  default; a delete would need a tombstone policy).
- Companies/organizations as first-class objects (only the contact's company
  *name* is synced today).
- Rate-limit backoff / retry on the HTTP adapters.
- Automatic CardDAV principal discovery.
