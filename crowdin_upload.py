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
RETRYABLE_HTTP = {429, 502, 503, 504}
ATTEMPTS = 6


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in RETRYABLE_HTTP
    return isinstance(exc, urllib.error.URLError)


class Crowdin:
    def __init__(self, token: str) -> None:
        self.headers = {"Authorization": f"Bearer {token}"}

    def request(
        self,
        path: str,
        method: str = "GET",
        data: bytes | None = None,
        headers=None,
        timeout: int = 120,
        retries: int = ATTEMPTS,
    ):
        last: BaseException | None = None
        for attempt in range(retries):
            request = urllib.request.Request(
                BASE + path,
                data=data,
                method=method,
                headers={**self.headers, **(headers or {})},
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    body = response.read()
                    return json.loads(body)["data"] if body else None
            except Exception as exc:
                last = exc
                if not _is_retryable(exc) or attempt == retries - 1:
                    raise
                if isinstance(exc, urllib.error.HTTPError):
                    exc.close()
                delay = min(2 ** attempt, 30)
                print(
                    f"Crowdin {method} {path} retry {attempt + 1}/{retries} "
                    f"after {exc}; sleep {delay}s",
                    flush=True,
                )
                time.sleep(delay)
        raise last  # pragma: no cover

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
            timeout=180,
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


def _selfcheck() -> None:
    assert _is_retryable(TimeoutError("read timed out"))
    class _Empty:
        def read(self, n: int = -1) -> bytes:
            return b""

        def close(self) -> None:
            return None

    busy = urllib.error.HTTPError("https://x", 429, "Too Many", None, _Empty())
    assert _is_retryable(busy)
    bad = urllib.error.HTTPError("https://x", 400, "Bad", None, _Empty())
    assert not _is_retryable(bad)
    assert _is_retryable(urllib.error.URLError(TimeoutError("t")))
    assert not _is_retryable(ValueError("no"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-only", action="store_true", help="skip active remote files")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("paths", nargs="*", type=Path, help="specific corpus files to upload")
    args = parser.parse_args()
    if args.self_check:
        _selfcheck()
        print("ok")
        return
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
        print(f"Uploading {remote_path}", flush=True)
        options = {
            "firstLineContainsHeader": True,
            "importTranslations": True,
            "scheme": SCHEME,
        }
        # ponytail: Crowdin storage IDs are single-use, so a timed-out PUT
        # cannot reuse the same id; re-upload storage on each attempt.
        last: BaseException | None = None
        for attempt in range(ATTEMPTS):
            try:
                storage_id = api.storage(path)
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
                        timeout=300,
                        retries=1,
                    )
                else:
                    if current and attempt == 0:
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
                    try:
                        api.request(
                            f"/projects/{PROJECT_ID}/files",
                            method="POST",
                            data=json.dumps(payload).encode(),
                            headers={"Content-Type": "application/json"},
                            timeout=300,
                            retries=1,
                        )
                    except urllib.error.HTTPError as error:
                        if error.code != 409:
                            raise
                        if attempt == ATTEMPTS - 1:
                            return True
                        time.sleep(attempt + 1)
                        continue
                return True
            except Exception as exc:
                last = exc
                if not _is_retryable(exc) or attempt == ATTEMPTS - 1:
                    raise RuntimeError(f"{remote_path}: {exc}") from exc
                delay = min(2 ** attempt, 30)
                print(
                    f"{remote_path} retry {attempt + 1}/{ATTEMPTS} "
                    f"after {exc}; sleep {delay}s",
                    flush=True,
                )
                time.sleep(delay)
        raise RuntimeError(f"{remote_path}: {last}") from last

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
