from datetime import datetime, timezone

from contacts_sync.matching import cluster_records
from contacts_sync.models import Contact, ContactRecord

NOW = datetime(2026, 6, 6, tzinfo=timezone.utc)


def rec(provider, rid, **kw):
    return ContactRecord(provider, rid, Contact(**kw), NOW)


def test_clusters_by_shared_email():
    records = [
        rec("hubspot", "1", first_name="David", emails=["d@x.com"]),
        rec("folk", "2", first_name="David R", emails=["d@x.com"]),
        rec("apple", "3", first_name="Someone", emails=["other@x.com"]),
    ]
    clusters = cluster_records(records)
    sizes = sorted(len(c) for c in clusters)
    assert sizes == [1, 2]


def test_singletons_survive():
    records = [
        rec("hubspot", "1", emails=["a@x.com"]),
        rec("folk", "2", emails=["b@x.com"]),
    ]
    assert len(cluster_records(records)) == 2


def test_prior_link_keeps_people_merged_without_shared_email():
    # Email removed from folk side, but a prior link ties them together.
    records = [
        rec("hubspot", "1", emails=["d@x.com"]),
        rec("folk", "2", first_name="David"),
    ]
    prior = [("rec:hubspot:1", "cluster-A"), ("rec:folk:2", "cluster-A")]
    clusters = cluster_records(records, prior_links=prior)
    assert len(clusters) == 1
