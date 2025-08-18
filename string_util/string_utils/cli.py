
import argparse
from .normalize import clean_text, normalize_case
from .validator import is_valid_email, is_strong_password

def main():
    parser = argparse.ArgumentParser(description="String Utilities CLI")
    parser.add_argument("command", choices=["clean", "normalize", "validate-email, validate-password,"])
    parser.add_argument("text", help="Input text")

    args = parser.parse_args()

    if args.command == "clean":
        print(clean_text(args.text))
    elif args.command == "normalize":
        print(normalize_case(args.text))
    elif args.command == "validate-email":
        print("✅ Valid" if is_valid_email(args.text) else "❌ Invalid")
    elif args.command == "validate-password":
        print("✅ Strong" if is_strong_password else "❌ weak" )

