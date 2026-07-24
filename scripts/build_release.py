"""Build reproducible archives for HACS and manual installation."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "air_threat_monitor"
DIST = ROOT / "dist"
HACS_ARCHIVE = DIST / "air-threat-monitor.zip"
MANUAL_DOCUMENTS = (
    "README.md",
    "RELEASE_TESTING.md",
    "CHANGELOG.md",
    "NOTICE.md",
    "LICENSE",
)
MANUAL_ASSET_DIRECTORIES = (
    ROOT / "brand",
    ROOT / "docs" / "images",
)


def _version() -> str:
    manifest = json.loads(
        (INTEGRATION / "manifest.json").read_text(encoding="utf-8")
    )
    version = manifest["version"]
    constants = (INTEGRATION / "const.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION: Final = "([^"]+)"$', constants, re.MULTILINE)
    if match is None or match.group(1) != version:
        raise RuntimeError("manifest.json and const.py versions do not match")
    return version


def _files() -> list[Path]:
    return sorted(
        path
        for path in INTEGRATION.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )


def _write_file(archive: ZipFile, source: Path, target: Path) -> None:
    info = ZipInfo(target.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, source.read_bytes())


def _build(archive_path: Path, *, manual: bool) -> None:
    with ZipFile(archive_path, "w") as archive:
        for source in _files():
            relative = source.relative_to(INTEGRATION)
            target = (
                Path("custom_components") / "air_threat_monitor" / relative
                if manual
                else relative
            )
            _write_file(archive, source, target)
        if manual:
            for filename in MANUAL_DOCUMENTS:
                _write_file(archive, ROOT / filename, Path(filename))
            for directory in MANUAL_ASSET_DIRECTORIES:
                for source in sorted(directory.rglob("*")):
                    if source.is_file():
                        _write_file(
                            archive,
                            source,
                            source.relative_to(ROOT),
                        )


def _validate_repository() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    if hacs.get("country") != "UA":
        raise RuntimeError("hacs.json must identify the supported country")
    if hacs.get("zip_release") is not True:
        raise RuntimeError("hacs.json must enable zip_release")
    if hacs.get("filename") != HACS_ARCHIVE.name:
        raise RuntimeError("hacs.json filename does not match the release archive")

    required = (
        ROOT / "README.md",
        ROOT / "NOTICE.md",
        ROOT / "brand" / "logo.png",
        ROOT / "brand" / "icon.png",
        INTEGRATION / "brand" / "icon.png",
        INTEGRATION / "brand" / "icon@2x.png",
        INTEGRATION / "manifest.json",
        INTEGRATION / "assets" / "air-threat-radar-card.js",
        ROOT / "docs" / "images" / "demo-safe-signal.png",
        ROOT / "docs" / "images" / "demo-alert-signal.png",
        ROOT / "docs" / "images" / "demo-safe-theme-dark.png",
        ROOT / "docs" / "images" / "demo-safe-theme-light.png",
        ROOT / "docs" / "images" / "card-editor.png",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing release files: {', '.join(missing)}")


def main() -> None:
    """Validate source metadata and build both archive layouts."""

    version = _version()
    _validate_repository()
    DIST.mkdir(exist_ok=True)
    for old_file in DIST.iterdir():
        if old_file.is_file():
            old_file.unlink()
        elif old_file.is_dir():
            shutil.rmtree(old_file)

    manual_archive = DIST / f"air-threat-monitor-{version}-manual.zip"
    _build(HACS_ARCHIVE, manual=False)
    _build(manual_archive, manual=True)

    checksums = []
    for archive in (HACS_ARCHIVE, manual_archive):
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        checksums.append(f"{digest}  {archive.name}")
    (DIST / "SHA256SUMS.txt").write_text(
        "\n".join(checksums) + "\n", encoding="utf-8"
    )

    print(f"Built Air Threat Monitor {version}")
    for archive in (HACS_ARCHIVE, manual_archive):
        print(f"- {archive.relative_to(ROOT)} ({archive.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
