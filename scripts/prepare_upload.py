"""Stage a complete storyboard snapshot in a Film Workbench upload session.

The Workbench validator checks hashes, MIME and dimensions. This helper only
checks the manifest-to-source mapping and copies each declared file once.
"""

import argparse
import json
import shutil
import time
from pathlib import Path, PurePosixPath


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def checked_entries(candidate: dict, sources: dict) -> list[tuple[Path, PurePosixPath]]:
    entries = candidate.get("files")
    if not isinstance(entries, list):
        raise ValueError("candidate.files must be an array")
    refs = [item.get("ref") for item in entries if isinstance(item, dict)]
    if len(refs) != len(entries) or len(set(refs)) != len(entries):
        raise ValueError("candidate files must have unique refs")
    if set(sources) != set(refs):
        raise ValueError("source map must contain exactly one source for every file ref")

    checked = []
    seen_paths = set()
    for item in entries:
        ref = item["ref"]
        rel_text = item["path"]
        if not isinstance(rel_text, str) or "\\" in rel_text:
            raise ValueError(f"Invalid file path for {ref}")
        rel = PurePosixPath(rel_text)
        if rel.is_absolute() or len(rel.parts) < 2 or rel.parts[0] != "files" or ".." in rel.parts:
            raise ValueError(f"File path must stay under files/: {rel_text}")
        if rel in seen_paths:
            raise ValueError(f"Duplicate file path: {rel_text}")
        seen_paths.add(rel)
        source = Path(sources[ref]).resolve(strict=True)
        if not source.is_file() or source.stat().st_size != item["bytes"]:
            raise ValueError(f"Missing file or size mismatch: {ref}")
        checked.append((source, rel))
    return checked


def checked_upload_dir(path: str, candidate: dict) -> Path:
    upload = Path(path).resolve(strict=True)
    if (
        upload.parent.name != "uploads"
        or upload.parent.parent.name != ".workbench"
        or not upload.name.startswith("UPL_")
    ):
        raise ValueError("Target must be one direct Workbench upload session")
    session = read_json(upload / "session.json")
    for field in ("project_id", "episode_id", "contract_version"):
        if session.get(field) != candidate.get(field):
            raise ValueError(f"Upload session {field} does not match candidate")
    if session.get("stage") != "storyboard" or candidate.get("artifact_type") != "storyboard":
        raise ValueError("This helper only accepts storyboard uploads")
    if session.get("consumed"):
        raise ValueError("Upload session has already been consumed")
    if (upload / "artifact.json").exists():
        raise ValueError("Upload session already contains artifact.json")
    files = upload / "files"
    if files.exists() and any(files.rglob("*")):
        raise ValueError("Upload session files/ is not empty")
    return upload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--source-map", type=Path, required=True)
    parser.add_argument("--upload-dir")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if not args.check_only and not args.upload_dir:
        parser.error("--upload-dir is required unless --check-only is set")

    candidate = read_json(args.candidate)
    sources = read_json(args.source_map)
    entries = checked_entries(candidate, sources)
    total_bytes = sum(source.stat().st_size for source, _ in entries)
    if args.check_only:
        print(json.dumps({"ok": True, "files": len(entries), "bytes": total_bytes, "copied": False}))
        return

    upload = checked_upload_dir(args.upload_dir, candidate)
    start = time.perf_counter()
    for source, rel in entries:
        target = upload.joinpath(*rel.parts)
        if not target.resolve().is_relative_to(upload):
            raise ValueError(f"Upload target escapes session: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(args.candidate, upload / "artifact.json")
    print(json.dumps({
        "ok": True,
        "files": len(entries),
        "bytes": total_bytes,
        "copy_seconds": round(time.perf_counter() - start, 3),
    }))


if __name__ == "__main__":
    main()
