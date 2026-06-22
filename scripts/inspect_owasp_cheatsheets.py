from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHEATSHEETS_DIR = ROOT / "data/raw/owasp_cheatsheet_series/cheatsheets"

print("OWASP Cheat Sheet Series Inspection")
print("=" * 70)
print(f"Path: {CHEATSHEETS_DIR}")
print(f"Exists: {CHEATSHEETS_DIR.exists()}")

md_files = sorted(CHEATSHEETS_DIR.glob("*.md"))

print(f"\nMarkdown files found: {len(md_files)}")
print("\nFirst 50 cheat sheets:")

for p in md_files[:50]:
    print("-", p.name)

keywords = [
    "SQL", "Injection", "Command", "XSS", "Cross_Site", "Input_Validation",
    "Authentication", "Authorization", "Access", "Password", "Secrets",
    "File_Upload", "SSRF", "Deserialization", "XXE", "XML", "Cryptographic",
    "Session", "Cookie", "CSRF", "Logging", "Error"
]

print("\nLikely relevant MVP cheat sheets:")
for p in md_files:
    name = p.name.lower()
    if any(k.lower() in name for k in keywords):
        print("-", p.name)
