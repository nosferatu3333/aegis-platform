"""Reproducible AEGIS Platform distribution bundles and integrity checks."""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from aegis_os.release import PLATFORM_VERSION, REPOSITORY_ROOT

_FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_MANIFEST_NAME = "DISTRIBUTION_MANIFEST.json"
_CHECKSUMS_NAME = "SHA256SUMS"


class DistributionError(RuntimeError):
    """Raised when a distribution bundle cannot be built or verified."""


@dataclass(frozen=True)
class DistributionFile:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class DistributionManifest:
    product: str
    platform_version: str
    source_commit: str
    source_tree: str
    source_branch: str
    files: tuple[DistributionFile, ...]
    execution_mode: str = "deterministic simulation only"
    real_world_effects_verified: bool = False

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["files"] = [asdict(item) for item in self.files]
        return payload

    def to_json_bytes(self) -> bytes:
        text = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        return text.encode("utf-8")


@dataclass(frozen=True)
class DistributionVerification:
    status: str
    bundle: str
    platform_version: str | None
    source_commit: str | None
    source_tree: str | None
    source_branch: str | None
    verified_files: int
    errors: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def _git(*arguments: str, root: Path = REPOSITORY_ROOT) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode:
        raise DistributionError(completed.stderr.strip() or "Git command failed.")
    return completed.stdout.strip()


def _tracked_paths(root: Path) -> tuple[Path, ...]:
    output = _git("ls-files", "-z", root=root)
    paths = [Path(item) for item in output.split("\0") if item]
    return tuple(sorted(paths, key=lambda item: item.as_posix()))


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, _FIXED_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def build_distribution_bundle(
    output_directory: Path,
    *,
    root: Path = REPOSITORY_ROOT,
) -> Path:
    """Build a deterministic source distribution with embedded provenance."""

    root = root.resolve()
    if _git("status", "--porcelain", root=root):
        raise DistributionError("Refusing to package a dirty repository.")

    commit = _git("rev-parse", "HEAD", root=root)
    tree = _git("rev-parse", "HEAD^{tree}", root=root)
    branch = _git("branch", "--show-current", root=root) or "detached"

    payloads: dict[str, bytes] = {}
    inventory: list[DistributionFile] = []
    for relative in _tracked_paths(root):
        absolute = root / relative
        if not absolute.is_file():
            continue
        archive_path = PurePosixPath("aegis-platform", relative.as_posix()).as_posix()
        payload = absolute.read_bytes()
        payloads[archive_path] = payload
        inventory.append(
            DistributionFile(
                path=archive_path,
                sha256=_sha256(payload),
                size=len(payload),
            )
        )

    manifest = DistributionManifest(
        product="AEGIS Platform",
        platform_version=PLATFORM_VERSION,
        source_commit=commit,
        source_tree=tree,
        source_branch=branch,
        files=tuple(inventory),
    )
    manifest_path = f"aegis-platform/{_MANIFEST_NAME}"
    payloads[manifest_path] = manifest.to_json_bytes()

    checksum_lines = [
        f"{_sha256(payloads[path])}  {path}" for path in sorted(payloads)
    ]
    checksums_path = f"aegis-platform/{_CHECKSUMS_NAME}"
    payloads[checksums_path] = ("\n".join(checksum_lines) + "\n").encode("utf-8")

    output_directory.mkdir(parents=True, exist_ok=True)
    bundle = output_directory / f"aegis-platform-{PLATFORM_VERSION}.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        for path in sorted(payloads):
            archive.writestr(_zip_info(path), payloads[path])
    return bundle


def verify_distribution_bundle(bundle: Path) -> DistributionVerification:
    """Verify embedded inventory and checksums without extracting the bundle."""

    errors: list[str] = []
    platform_version: str | None = None
    source_commit: str | None = None
    source_tree: str | None = None
    source_branch: str | None = None
    verified = 0
    try:
        with zipfile.ZipFile(bundle) as archive:
            names = set(archive.namelist())
            manifest_path = f"aegis-platform/{_MANIFEST_NAME}"
            checksums_path = f"aegis-platform/{_CHECKSUMS_NAME}"
            if manifest_path not in names or checksums_path not in names:
                raise DistributionError("Bundle metadata is incomplete.")

            manifest = json.loads(archive.read(manifest_path))
            platform_version = manifest.get("platform_version")
            source_commit = manifest.get("source_commit")
            source_tree = manifest.get("source_tree")
            source_branch = manifest.get("source_branch")
            for entry in manifest.get("files", []):
                path = entry["path"]
                if path not in names:
                    errors.append(f"missing:{path}")
                    continue
                payload = archive.read(path)
                if len(payload) != entry["size"]:
                    errors.append(f"size:{path}")
                    continue
                if _sha256(payload) != entry["sha256"]:
                    errors.append(f"sha256:{path}")
                    continue
                verified += 1

            for line in archive.read(checksums_path).decode("utf-8").splitlines():
                expected, path = line.split("  ", 1)
                if path not in names:
                    errors.append(f"checksum-missing:{path}")
                elif _sha256(archive.read(path)) != expected:
                    errors.append(f"checksum:{path}")
    except (
        DistributionError,
        OSError,
        zipfile.BadZipFile,
        KeyError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        errors.append(str(error))

    return DistributionVerification(
        status="verified" if not errors else "invalid",
        bundle=str(bundle.resolve()),
        platform_version=platform_version,
        source_commit=source_commit,
        source_tree=source_tree,
        source_branch=source_branch,
        verified_files=verified,
        errors=tuple(errors),
    )
