import  regex as re

def clean_text(text: str) -> str:
    """Convert multiple spaces into one and strip leading/trailing spaces"""
    return re.sub(r'\s+', ' ', text).strip()

def normalize_case(text: str) -> str:
    return text.lower()
