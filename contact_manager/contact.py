from dataclasses import asdict, dataclass, field
from typing import ClassVar, Dict
import re
import uuid

@dataclass
class Contact:
    cid: uuid.UUID = field(default_factory=uuid.uuid4())
    cname: str
    phone: str
    email: str

    EMAIL_RE: ClassVar[re.Pattern] = re.compile(r"[^@]+@[^@]+\.[^@]+")

    def __post_init__(self):
        """Runs after the dataclass generated __init__. 
        Use it for normalization and validation"""
        # normalize strings (strip whitespace)
        self.cname = self.cname.strip()
        self.phone = self.phone.strip()
        self.email = self.email.strip()
         
        #validation
        if not self.cname:
            raise ValueError("name must not be empty")
        if not self.phone:
            raise ValueError("phone must not be empty")
        if not self.EMAIL_RE.fullmatch(self.email):
            raise ValueError("email must not be empty")
        
    def to_Dict(self) -> Dict[str, str]:
        """Return a plain dict suitable for serializing (CSV, pandas, json)"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Contact" :
        """Create Contact from a dict produced by to_dict or read from CSV/pandas."""
        # This will raise a KeyError if required keys are missing — explicit is good.
        return cls(cname=data["cname"], phone=data["phone"], email=data["email"])
    
    def __str__(self):
         """User-friendly string for printing (overrides dataclass default)."""
         return(f"{self.cname} | {self.phone} | {self.email}")