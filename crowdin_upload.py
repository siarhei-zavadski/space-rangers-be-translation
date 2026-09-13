#!/usr/bin/env python3
"""Upload split TSV sources with the schema Crowdin CLI omits for new files."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from urllib.parse import quote

ROOT = Path(__file__).parent
LANG_DIR = ROOT / "crowdin/lang_dat"
QUEST_DIR = ROOT / "crowdin/quests"
ROBOTS_DIR = ROOT / "crowdin/robots"
ASSET_DIR = ROOT / "crowdin/assets"
PROJECT_ID = 930019
BASE = "https://api.crowdin.com/api/v2"
SCHEME = {"identifier": 0, "sourcePhrase": 1, "context": 2, "labels": 3, "be": 4}


class Crowdin:
    def __init__(self, token: str) -> None:
        self.headers = {"Authorization": f"Bearer {token}"}

    def request(self, path: str, method: str = "GET", data: bytes | None = None, headers=None):
        request = urllib.request.Request(
            BASE + path,
            data=data,
            method=method,
            headers={**self.headers, **(headers or {})},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
            return json.loads(body)["data"] if body else None

    def pages(self, path: str) -> list[dict]:
        result = []
        offset = 0
        while True:
            separator = "&" if "?" in path else "?"
            batch = self.request(f"{path}{separator}limit=500&offset={offset}")
            result.extend(batch)
            if len(batch) < 500:
                return result
            offset += 500

    def storage(self, path: Path) -> int:
        return self.request(
            "/storages",
            method="POST",
            data=path.read_bytes(),
            headers={
                "Content-Type": "text/tab-separated-values; charset=utf-8",
                "Crowdin-API-FileName": quote(path.name),
            },
        )["id"]


def local_files(selected: list[Path]) -> list[Path]:
    if selected:
        return [path.resolve() for path in selected]
    return sorted((
        *LANG_DIR.glob("*.tsv"),
        *QUEST_DIR.glob("*.tsv"),
        *ROBOTS_DIR.glob("*.tsv"),
        *ASSET_DIR.glob("*.tsv"),
    ))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-only", action="store_true", help="skip active remote files")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("paths", nargs="*", type=Path, help="specific corpus files to upload")
    args = parser.parse_args()
    token = os.environ.get("CROWDIN_PERSONAL_TOKEN")
    if not token:
        raise SystemExit("Set CROWDIN_PERSONAL_TOKEN")
    api = Crowdin(token)
    remote = {
        row["data"]["path"]: row["data"]
        for row in api.pages(f"/projects/{PROJECT_ID}/files")
    }

    def upload(path: Path) -> bool:
        remote_path = "/" + path.relative_to(Path(__file__).parent).as_posix()
        current = remote.get(remote_path)
        if current and current["status"] == "active" and args.new_only:
            return False
        storage_id = api.storage(path)
        options = {
            "firstLineContainsHeader": True,
            "importTranslations": True,
            "scheme": SCHEME,
        }
        if current and current["status"] == "active":
            payload = {
                "storageId": storage_id,
                "updateOption": "keep_translations_and_approvals",
                "importOptions": options,
            }
            api.request(
                f"/projects/{PROJECT_ID}/files/{current['id']}",
                method="PUT",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
        else:
            if current:
                api.request(
                    f"/projects/{PROJECT_ID}/files/{current['id']}",
                    method="DELETE",
                )
                time.sleep(0.5)
            directory_path = str(Path(remote_path).parent)
            directories = {
                row["data"]["path"]: row["data"]["id"]
                for row in api.pages(f"/projects/{PROJECT_ID}/directories")
            }
            payload = {
                "storageId": storage_id,
                "name": path.name,
                "directoryId": directories[directory_path],
                "type": "csv",
                "importOptions": options,
            }
            for attempt in range(5):
                try:
                    api.request(
                        f"/projects/{PROJECT_ID}/files",
                        method="POST",
                        data=json.dumps(payload).encode(),
                        headers={"Content-Type": "application/json"},
                    )
                    break
                except urllib.error.HTTPError as error:
                    if error.code != 409 or attempt == 4:
                        raise
                    time.sleep(attempt + 1)
        return True

    uploaded = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(upload, path) for path in local_files(args.paths)]
        for future in as_completed(futures):
            uploaded += future.result()
            if uploaded and uploaded % 20 == 0:
                print(f"Uploaded {uploaded} files")
    print(f"Uploaded {uploaded} source files")
    try:
        progress = api.request(f"/projects/{PROJECT_ID}/languages/progress")
    except Exception as exc:  # ponytail: progress is a recheck, not a gate
        print(f"Crowdin progress unavailable: {exc}")
        return
    for row in progress or []:
        data = row["data"] if isinstance(row, dict) and "data" in row else row
        phrases = data.get("phrases") or {}
        print(
            f"Crowdin {data.get('languageId')}: "
            f"{data.get('translationProgress')}% translated, "
            f"{data.get('approvalProgress')}% approved "
            f"({phrases.get('translated', '?')}/{phrases.get('total', '?')} phrases)"
        )


if __name__ == "__main__":
    main()
