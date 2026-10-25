import hashlib
def test_one_byte_change_changes_sha256():
    original=b"synthetic FIR sample: section 420"
    changed=b"synthetic FIR sample: section 421"
    assert hashlib.sha256(original).hexdigest()!=hashlib.sha256(changed).hexdigest()
def test_empty_input_hash_is_not_empty_digest():
    assert hashlib.sha256(b"").hexdigest() != ""
