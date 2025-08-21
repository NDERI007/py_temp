import uuid
from contact_book import ContactBook, Contact

def test_contactAddition():
    #create an instance
    contact_book = ContactBook()

     #create a contact
    contact = Contact(cname="alice", phone="123", email="test@example.com")

    contact_book.add_contact(contact)

    assert contact.cid in contact_book._contact
    assert contact_book._contact[contact.cid].cname == "alice"

def test_removeContact():
    #create an instance
    contact_book = ContactBook()

     #create a contact
    contact = Contact(cname="alice", phone="123", email="test@example.com")

    contact_book.add_contact(contact)

    assert contact.cid in contact_book._contact

    contact_book.remove_contact(contact)

    #assert it's gone
    assert contact.cid not in contact_book._contact

def test_remove_contact_nonexistent():
    """Test removing a contact that doesn't exist (should not crash)."""
    # Setup
    contact_book = ContactBook()
    contact = Contact(cname="ghost", phone="000", email="ghost@example.com")
    
    # Try to remove contact that was never added (should not crash)
    contact_book.remove_contact(contact)  # Should do nothing gracefully
    
    # Verify book is still empty
    assert len(contact_book._contact) == 0
    
def test_getting_EXISTING_Contact():
    """Test getting a contact that exists."""
    contact_book = ContactBook()

     #create a contact
    contact = Contact(cname="alice", phone="123", email="test@example.com")

    contact_book.add_contact(contact)

    assert contact.cid in contact_book._contact

    retrieved = contact_book.get_contact(contact.cid)
      
    assert retrieved is not None
    assert retrieved.cname == "alice"
    assert retrieved.phone == "123"
    assert retrieved.email == "test@example.com"
    assert retrieved.cid == contact.cid

def test_getting_NONEXISTANT_CONTACT():
    """Test getting a contact that doesn't exist."""
    contact_book = ContactBook()

    fakeID = uuid.uuid4()
    result = contact_book.get_contact(fakeID)

    assert result is None

def test_search_for_exact_match():
    """Test searching for a contact with exact name match."""
    # Setup
    contact_book = ContactBook()
    alice = Contact(cname="Alice", phone="123", email="alice@example.com")
    bob = Contact(cname="Bob", phone="456", email="bob@example.com")
    contact_book.add_contact(alice)
    contact_book.add_contact(bob)
    
    # Search for Alice
    results = contact_book.search_for("Alice")
    
    # Should find exactly Alice
    assert len(results) == 1
    assert results[0].cname == "Alice"


def test_search_for_case_insensitive():
    """Test that search is case insensitive."""
    # Setup
    contact_book = ContactBook()
    alice = Contact(cname="Alice", phone="123", email="alice@example.com")
    contact_book.add_contact(alice)
    
    # Search with different cases
    results_lower = contact_book.search_for("alice")
    results_upper = contact_book.search_for("ALICE")
    results_mixed = contact_book.search_for("aLiCe")
    
    # All should find Alice
    assert len(results_lower) == 1
    assert len(results_upper) == 1
    assert len(results_mixed) == 1
    assert results_lower[0].cname == "Alice"
    assert results_upper[0].cname == "Alice"
    assert results_mixed[0].cname == "Alice"


def test_search_for_no_matches():
    """Test searching for a name that doesn't exist."""
    # Setup
    contact_book = ContactBook()
    alice = Contact(cname="Alice", phone="123", email="alice@example.com")
    contact_book.add_contact(alice)
    
    # Search for non-existent name
    results = contact_book.search_for("Charlie")
    
    # Should return empty list
    assert len(results) == 0
    assert results == []


def test_search_for_multiple_matches():
    """Test searching when multiple contacts have the same name."""
    # Setup
    contact_book = ContactBook()
    alice1 = Contact(cname="Alice", phone="123", email="alice1@example.com")
    alice2 = Contact(cname="Alice", phone="456", email="alice2@example.com")
    bob = Contact(cname="Bob", phone="789", email="bob@example.com")
    
    contact_book.add_contact(alice1)
    contact_book.add_contact(alice2)
    contact_book.add_contact(bob)
    
    # Search for Alice
    results = contact_book.search_for("Alice")
    
    # Should find both Alices
    assert len(results) == 2
    names = [contact.cname for contact in results]
    assert all(name == "Alice" for name in names)


def test_list_contacts_empty():
    """Test listing contacts when book is empty."""
    # Setup
    contact_book = ContactBook()
    
    # List contacts
    contacts = contact_book.list_contacts()
    
    # Should return empty list
    assert contacts == []
    assert len(contacts) == 0


def test_list_contacts_with_data():
    """Test listing contacts when book has contacts."""
    # Setup
    contact_book = ContactBook()
    alice = Contact(cname="Alice", phone="123", email="alice@example.com")
    bob = Contact(cname="Bob", phone="456", email="bob@example.com")
    charlie = Contact(cname="Charlie", phone="789", email="charlie@example.com")
    
    contact_book.add_contact(alice)
    contact_book.add_contact(bob)
    contact_book.add_contact(charlie)
    
    # List contacts
    contacts = contact_book.list_contacts()
    
    # Should return all 3 contacts
    assert len(contacts) == 3
    
    # Verify all contacts are there (order doesn't matter)
    names = [contact.cname for contact in contacts]
    assert "Alice" in names
    assert "Bob" in names
    assert "Charlie" in names


def test_list_contacts_returns_copy():
    """Test that list_contacts returns a new list (not the internal dict values)."""
    # Setup
    contact_book = ContactBook()
    alice = Contact(cname="Alice", phone="123", email="alice@example.com")
    contact_book.add_contact(alice)
    
    # Get the list
    contacts1 = contact_book.list_contacts()
    contacts2 = contact_book.list_contacts()
    
    # Should be different list objects (but same content)
    assert contacts1 is not contacts2  # Different objects
    assert contacts1 == contacts2      # Same content

def test_update_existing_contact():

    contact_book =ContactBook()
    alice = Contact(cname="Alice", phone="123", email="alice@example.com")
    contact_book.add_contact(alice)

    contact_book.update_contacts(alice.cid, email="kev@sexample.com")

    assert alice.email is not "alice@example.com"  # unchanged
