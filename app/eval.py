from __future__ import annotations

import argparse
import json
from pathlib import Path

from .guard import canonical


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true")
    parser.parse_args()
    posts = json.loads((Path(__file__).resolve().parents[1] / "data" / "posts.json").read_text(encoding="utf-8"))
    labeled = [post for post in posts if post["subject"] != "glacier"]
    print(json.dumps({"labeled_posts": len(labeled), "metric": "top1_precision", "note": "Run against the live API after catalog processing."}, indent=2))


if __name__ == "__main__":
    main()

