"""Compare every published site file against what the live domain serves.

Reads the file list from the publishing clone's index (what was pushed), fetches
each path from the live site, and reports any byte difference. This is how a
file that was edited locally but never published shows up.
"""

import hashlib
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

UPSTREAM = Path("/tmp/ctt_upstream")
SITE = Path("/projects/conference-program/projects/ctt_website")
LIVE = "https://chloestravellingtutors.com/"
SKIP_DIRS = {".git", ".supervisor", "inputs", "output", "work", "tests", "scripts"}


def tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=UPSTREAM, capture_output=True, text=True
    ).stdout.split("\n")
    return [p for p in out if p and not p.startswith(tuple(f"{d}/" for d in SKIP_DIRS))]


def fetch(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        return f"HTTP {error.code}".encode()
    except Exception as error:  # noqa: BLE001
        return f"ERR {error}".encode()


def main() -> int:
    paths = tracked()
    print(f"checking {len(paths)} published files against {LIVE}")
    mismatches = []
    for rel in paths:
        local = UPSTREAM / rel
        if not local.exists():
            mismatches.append((rel, "missing locally"))
            continue
        want = hashlib.sha256(local.read_bytes()).hexdigest()
        got = hashlib.sha256(fetch(LIVE + rel) or b"").hexdigest()
        if want != got:
            mismatches.append((rel, "differs"))
    print(f"mismatches: {len(mismatches)}")
    for rel, why in mismatches:
        print(f"  {why:<18} {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
