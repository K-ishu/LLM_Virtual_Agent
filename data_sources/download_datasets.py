"""Download public online datasets once and store them locally.

This project does not depend on live web checks during normal execution. Run
this script during setup to populate data/raw, then run prepare_benchmark.py to
create a reproducible local corpus under data/processed.

Run:
    python data_sources/download_datasets.py
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SourceRecord:
    name: str
    source_url: str
    local_files: list[str]
    notes: str


def _stream_download(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with output_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)


def download_zenodo_record(record_id: str, folder_name: str) -> SourceRecord:
    """Download all files from a public Zenodo record via the Zenodo API."""
    api_url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(api_url, timeout=60)
    response.raise_for_status()
    record = response.json()

    target_dir = RAW_DIR / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    local_files: list[str] = []
    for file_obj in record.get("files", []):
        file_name = file_obj.get("key") or file_obj.get("filename")
        links = file_obj.get("links", {})
        download_url = links.get("self") or links.get("download")
        if not file_name or not download_url:
            continue
        output_path = target_dir / file_name
        if not output_path.exists():
            print(f"Downloading {file_name} from Zenodo record {record_id}...")
            _stream_download(download_url, output_path)
        local_files.append(str(output_path.relative_to(PROJECT_ROOT)))

    return SourceRecord(
        name=record.get("metadata", {}).get("title", f"Zenodo record {record_id}"),
        source_url=f"https://zenodo.org/records/{record_id}",
        local_files=local_files,
        notes="Downloaded through the Zenodo public API.",
    )


def download_owasp_static_files() -> Iterable[SourceRecord]:
    files = {
        "user-security-stories.md": "https://raw.githubusercontent.com/OWASP/user-security-stories/master/user-security-stories.md",
        "security-acceptance-criteria.md": "https://raw.githubusercontent.com/OWASP/user-security-stories/master/security-acceptance-criteria.md",
    }
    local_files: list[str] = []
    target_dir = RAW_DIR / "owasp_user_security_stories"
    for file_name, url in files.items():
        output_path = target_dir / file_name
        if not output_path.exists():
            print(f"Downloading OWASP {file_name}...")
            _stream_download(url, output_path)
        local_files.append(str(output_path.relative_to(PROJECT_ROOT)))

    yield SourceRecord(
        name="OWASP user security stories",
        source_url="https://github.com/OWASP/user-security-stories",
        local_files=local_files,
        notes="Downloaded from GitHub raw content. Repository license: Apache-2.0 at the time this project was prepared.",
    )


def write_manual_download_notes() -> SourceRecord:
    """Create instructions for datasets whose portal lacks a stable direct URL."""
    target_dir = RAW_DIR / "fr_nfr_dataset"
    target_dir.mkdir(parents=True, exist_ok=True)
    notes_path = target_dir / "README_MANUAL_DOWNLOAD.md"
    notes_path.write_text(
        """# Manual dataset download: FR_NFR_dataset

The FR_NFR_dataset is hosted by Mendeley Data:
https://data.mendeley.com/datasets/4ysx9fyzv4/1

The portal may require a browser session and may not expose a stable direct
file URL suitable for automated download. Download the dataset manually and
place the file(s) in this folder:

```text
data/raw/fr_nfr_dataset/
```

Supported file formats in `prepare_benchmark.py`:

- `.csv`
- `.tsv`
- `.txt`
- `.xlsx` or `.xls` if `openpyxl` is installed

Keep the original filename and preserve the original source citation in the
final report.
""",
        encoding="utf-8",
    )
    return SourceRecord(
        name="FR_NFR_dataset",
        source_url="https://data.mendeley.com/datasets/4ysx9fyzv4/1",
        local_files=[str(notes_path.relative_to(PROJECT_ROOT))],
        notes="Manual download note written because the Mendeley Data portal may not expose a stable direct file URL.",
    )


def main() -> None:
    manifest: list[SourceRecord] = []
    manifest.append(download_zenodo_record("1414117", "pure_requirements"))
    manifest.append(download_zenodo_record("13880060", "user_stories"))
    manifest.extend(download_owasp_static_files())
    manifest.append(write_manual_download_notes())

    manifest_path = RAW_DIR / "sources_manifest.json"
    manifest_path.write_text(
        json.dumps([asdict(item) for item in manifest], indent=2),
        encoding="utf-8",
    )
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
