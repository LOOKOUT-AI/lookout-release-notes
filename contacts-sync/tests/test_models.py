from contacts_sync.models import Contact, normalize_email, normalize_phone


def test_normalization():
    assert normalize_email("  David@Lookout.TEAM ") == "david@lookout.team"
    assert normalize_phone("+1 (415) 555-0100") == "+14155550100"
    assert normalize_phone("415.555.0100") == "4155550100"


def test_contact_dedupes_and_strips():
    c = Contact(first_name=" David ", emails=["A@x.com", "a@x.com"], phones=["+1 5", "+15"])
    assert c.first_name == "David"
    assert c.emails == ["a@x.com"]
    assert c.phones == ["+15"]


def test_content_hash_is_order_independent():
    a = Contact(emails=["a@x.com", "b@x.com"])
    b = Contact(emails=["b@x.com", "a@x.com"])
    assert a.content_hash() == b.content_hash()


def test_match_keys_use_email_only():
    c = Contact(first_name="David", last_name="Rose", emails=["d@x.com"])
    assert c.match_keys() == {"email:d@x.com"}


def test_merge_prefers_incoming_scalars_and_unions_lists():
    base = Contact(first_name="Dave", company="Old", emails=["a@x.com"])
    incoming = Contact(first_name="David", title="CEO", emails=["b@x.com"])
    merged = Contact.merge(base, incoming)
    assert merged.first_name == "David"      # incoming wins
    assert merged.company == "Old"           # preserved (incoming empty)
    assert merged.title == "CEO"             # added
    assert merged.emails == ["b@x.com", "a@x.com"]  # union, incoming primary first
