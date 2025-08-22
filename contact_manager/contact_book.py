import os
import tempfile
import uuid
import pandas as pd
from tabulate import tabulate
from contact import Contact
from typing import Dict

class ContactBook:
    ALLOWED_UPDATE_FIELDS = {"cname","phone", "email"} #whitelist

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
    
    def update_contacts(self, contact_id:uuid.UUID, **kwargs):
        """
        Update fields of a contact. Allowed fields: cname, phone, email.
        Returns True if updated, False if contact not found.
        """
        contact= self.get_contact(contact_id)
        if not contact:
           return False
        
        original = {field: getattr(contact, field) for field in self.ALLOWED_UPDATE_FIELDS}

        #update only valid attr
        for field_name, value in kwargs.items():
         if field_name in self.ALLOWED_UPDATE_FIELDS :
            setattr(contact, field_name, value.strip() if isinstance(value, str) else value)

        # re-run validation (reuse __post_init__)
        try:
           contact.__post_init__()
        except ValueError as e:
           print(f"Update failed {e}")

           for field, oldValue in original.items():
              setattr(contact, field, oldValue)
           return False
        return True
    
    def save_to_Panda(self, filename:str) -> int:
        """
         Save contacts to CSV using pandas. Returns number of contacts saved.
          Uses an atomic write (write to temp file then os.replace).
         The CSV columns: cname, phone, email, cid
        """
        # 1) Ensure the destination directory exists
        dirn= os.path.dirname(filename) or "."
        os.makedirs(dirn, exist_ok=True)

        rows=[]
        for c in self._contact.values():
           d= c.to_Dict()
           d["cid"]= str(d["cid"]) # UUID → str
           rows.append(d) #add to the end of the list

         # 3) Build DataFrame (stable column order even if rows = [])
        df = pd.DataFrame(rows, columns=["cname","phone","email","cid"])

         # 4) Create a temp file in the same dir (required for atomic replace)
        fd, tmpname= tempfile.mkstemp(prefix="contacts_", dir=dirn, text=True)
        os.close(fd)

        try:
           df.to_csv(tmpname, index=False, encoding="UTF-8")
           os.replace(tmpname, filename) # atomic on most OSes
           return len(df)
        except Exception:
           # cleanup temp file if something failed
           try:
            os.remove(tmpname)
           except Exception:
            pass
           raise

    def load_contact_pandas(self, filename:str, show_table:bool =True) -> int:
        """
        Load contacts from CSV into the ContactBook using pandas.
        Returns the number of contacts loaded.
        Optionally prints them in a tabulated format.
        """
        try:
           df = pd.read_csv(filename, encoding="UTF-8")

           # Clear old contacts and repopulate
           self._contact.clear()

           for _, row in df.iterrows():
              c= Contact(
                 cname=row["cname"],
                 phone=str(row["phone"]),
                 email=row["email"],
              )
              # If CSV had cid, keep it
              if "cid" in row and pd.notna(row["cid"]):
                 c.cid = row["cid"]
                 self._contact[c.cid] = c

            # Show table if requested
              if show_table:
               print(tabulate(df, headers="keys", tablefmt="orgtbl"))

               return len(self._contact)

        except FileNotFoundError:
         print(f"❌ File not found: {filename}")
         return 0
        except Exception as e:
               print(f"❌ Error loading contacts: {e}")
               return 0
        
contact_book =ContactBook()
alice = Contact(cname="Alice", phone="123", email="alice@example.com")
bob = Contact(cname="Bob", phone="456", email="bob@example.com")
contact_book.add_contact(alice)
contact_book.add_contact(bob)

filename= "contact.csv"

#count= contact_book.save_to_Panda(str(filename))
count1 = contact_book.load_contact_pandas(str(filename))
