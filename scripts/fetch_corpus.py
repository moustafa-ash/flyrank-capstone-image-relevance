"""Download the pinned Pexels manifest and write a reproducible SHA-256 lock."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "corpus.json"
IMAGE_DIR = ROOT / "data" / "images"
LOCK = ROOT / "data" / "corpus.lock.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    locked = []
    for image in manifest["images"]:
        destination = IMAGE_DIR / f"{image['id']}.jpg"
        request = Request(image["image_url"], headers={"User-Agent": "flyrank-capstone/1.0"})
        with urlopen(request, timeout=30) as response:
            payload = response.read()
        destination.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        locked.append({**image, "sha256": digest, "local_file": destination.relative_to(ROOT).as_posix()})
        print(f"{image['id']} {len(payload)} bytes sha256={digest}")
    LOCK.write_text(json.dumps({"manifest_version": manifest["version"], "images": locked}, indent=2) + "\n", encoding="utf-8")
    print(f"locked {len(locked)} images -> {LOCK}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"corpus download failed: {exc}", file=sys.stderr)
        raise

