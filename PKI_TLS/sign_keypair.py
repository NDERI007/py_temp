import argparse
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel

console = Console()

def ed_gen_key():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes( #serializes the private key into bytes.
        encoding= serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8, #PKCS#8 is a widely used standard wrapper for private keys (good for interoperability).
        encryption_algorithm=serialization.NoEncryption(), #the PEM is written unencrypted (no password). Convenient for demos, not recommended for long-term secrets.
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo #SubjectPublicKeyInfo (SPKI) is the standard format for public keys (what certs use).
    )

    with open("private.pem", "wb") as f:
        f.write(private_pem)

    with open("public.pem", "wb") as f:
        f.write(public_pem)

    console.print(
        Panel.fit(
            "[bold green] ✅ Ed25519 keypair generated [/bold green]\n"
            "Saved as: [cyan]private.pem[/cyan] + [cyan]public.pem[/cyan]",
            border_style="green"
        )
    )

def inspect_keys():
    # Load private key
    with open("private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Load public key
    with open("public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    # Build a table
    table = Table(title="🔑 Ed25519 Key Information")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Details", style="white")

    # Private key details
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    table.add_row("Private key", private_bytes.hex())

    # Public key details
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    table.add_row("Public key", public_bytes.hex())

    console.print(table)

    # Also print the actual PEMs with nice syntax highlighting
    with open("private.pem") as f:
        console.print(Syntax(f.read(), "pem", theme="monokai", line_numbers=True))

    with open("public.pem") as f:
        console.print(Syntax(f.read(), "pem", theme="monokai", line_numbers=True))

    
if __name__ == "__main__": #Standard Python “main guard” so the script runs when executed directly.
    parser = argparse.ArgumentParser(description="Key management tool")
    parser.add_argument("command", choices=["gen-ed", "inspect"], help="command to run")
    args = parser.parse_args()

    if args.command == "gen-ed":
        ed_gen_key()
    elif args.command == "inspect":
        inspect_keys()