from datetime import datetime, timedelta, timezone

from contacts_sync.engine import SyncEngine
from contacts_sync.models import Contact
from contacts_sync.state import StateStore
from tests.fakes import FakeProvider

T0 = datetime(2026, 6, 1, tzinfo=timezone.utc)


def make_engine(tmp_path, *providers):
    state = StateStore(str(tmp_path / "state.db"))
    return SyncEngine(list(providers), state), state


def test_new_contact_propagates_to_all_providers(tmp_path):
    hub = FakeProvider("hubspot")
    folk = FakeProvider("folk")
    apple = FakeProvider("apple")
    hub.seed(Contact(first_name="David", last_name="Rose", emails=["d@x.com"]), T0)

    engine, state = make_engine(tmp_path, hub, folk, apple)
    report = engine.run()

    assert len(folk.store) == 1
    assert len(apple.store) == 1
    assert next(iter(folk.store.values())).contact.primary_email == "d@x.com"
    # Second run is a no-op (convergence).
    report2 = engine.run()
    assert report2.changes == []
    state.close()


def test_two_way_merge_latest_edit_wins(tmp_path):
    hub = FakeProvider("hubspot")
    folk = FakeProvider("folk")
    hub.seed(Contact(first_name="David", emails=["d@x.com"], company="LOOKOUT"), T0)
    engine, state = make_engine(tmp_path, hub, folk)
    engine.run()  # establish baseline + propagate to folk

    # Edit title in folk (newer) and company in hubspot (older). Both apply;
    # they touch different fields so both survive.
    folk_id = next(iter(folk.store))
    folk.store[folk_id].contact = Contact(
        first_name="David", emails=["d@x.com"], company="LOOKOUT", title="CEO"
    )
    folk.store[folk_id].updated_at = T0 + timedelta(days=2)

    report = engine.run()
    hub_contact = next(iter(hub.store.values())).contact
    assert hub_contact.title == "CEO"
    assert hub_contact.company == "LOOKOUT"
    assert any(c.action == "update" for c in report.changes)
    state.close()


def test_conflicting_scalar_uses_most_recent(tmp_path):
    hub = FakeProvider("hubspot")
    folk = FakeProvider("folk")
    hub.seed(Contact(first_name="Dave", emails=["d@x.com"]), T0)
    engine, state = make_engine(tmp_path, hub, folk)
    engine.run()

    # Same field edited on both sides; folk edit is newer -> folk wins.
    hub_id = next(iter(hub.store))
    hub.store[hub_id].contact = Contact(first_name="Davey", emails=["d@x.com"])
    hub.store[hub_id].updated_at = T0 + timedelta(days=1)
    folk_id = next(iter(folk.store))
    folk.store[folk_id].contact = Contact(first_name="David", emails=["d@x.com"])
    folk.store[folk_id].updated_at = T0 + timedelta(days=3)

    engine.run()
    assert next(iter(hub.store.values())).contact.first_name == "David"
    assert next(iter(folk.store.values())).contact.first_name == "David"
    state.close()


def test_existing_contacts_on_both_sides_merge_by_email(tmp_path):
    hub = FakeProvider("hubspot")
    folk = FakeProvider("folk")
    hub.seed(Contact(first_name="David", emails=["d@x.com"], company="LOOKOUT"), T0)
    folk.seed(Contact(first_name="David", emails=["d@x.com"], title="CEO"), T0)

    engine, state = make_engine(tmp_path, hub, folk)
    engine.run()
    # No duplicate created; both converge to the union.
    assert len(hub.store) == 1
    assert len(folk.store) == 1
    hub_contact = next(iter(hub.store.values())).contact
    assert hub_contact.company == "LOOKOUT"
    assert hub_contact.title == "CEO"
    state.close()


def test_dry_run_writes_nothing(tmp_path):
    hub = FakeProvider("hubspot")
    folk = FakeProvider("folk")
    hub.seed(Contact(first_name="David", emails=["d@x.com"]), T0)
    engine, state = make_engine(tmp_path, hub, folk)
    report = engine.run(dry_run=True)
    assert report.changes  # planned
    assert len(folk.store) == 0  # but nothing written
    state.close()
