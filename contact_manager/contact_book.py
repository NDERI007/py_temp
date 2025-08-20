import uuid
from contact import Contact
from typing import Dict

class ContactBook:
    def __init__(self):
        #Encapsulation is achieved by the single leading underscore _
        self._contact : Dict[uuid.UUID, Contact] = {}

    def add_contact(self, contact:Contact):
        """Add a new contact to the book."""
        self._contact[contact.cid] = contact

    def remove_contact(self, contact:Contact):
        """Remove a contact by id."""
        if contact.cid in self._contact:
         del self._contact[contact.cid]

    def get_contact(self, contact_id:uuid.UUID) -> Contact | None:
        return self._contact.get(contact_id)
    
    def search_for(self, name:str):
        return [ c for c in self._contact.values() if c.cname.lower() == name.lower()]
    
    def list_contacts(self):
        return list(self._contact.values())