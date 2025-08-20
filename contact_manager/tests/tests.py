import pytest
from contact import Contact

def test_dataclass_equality_and_repr():
    a = Contact("Alice", "123", "alice@example.com")
    b = Contact("Alice", "123", "alice@example.com")
    assert a == b
    assert "Alice" in repr(a)

def test_str_format():
    c = Contact("Bob", "456", "bob@example.com")
    assert str(c) == "Bob | 456 | bob@example.com"

def test_to_dict_and_from_dict_roundtrip():
    c1 = Contact(" Carol ", " 789 ", " carol@example.com ")
    d = c1.to_Dict()
    # keys present and normalized (post_init strips whitespace)
    assert d == {"cname": "Carol", "phone": "789", "email": "carol@example.com"}
    c2 = Contact.from_dict(d)
    assert c2 == Contact("Carol", "789", "carol@example.com")

def test_validation_empty_name():
    with pytest.raises(ValueError):
        Contact("   ", "123", "a@b.com")

def test_validation_invalid_email():
    with pytest.raises(ValueError):
        Contact("Dan", "123", "not-an-email")

def test_validation_empty_phone():
    with pytest.raises(ValueError):
        Contact("Eve", "   ", "eve@example.com")