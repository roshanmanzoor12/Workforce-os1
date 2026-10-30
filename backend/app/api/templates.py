from __future__ import annotations

import os
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import HTTPException

from app.models.template import (
    TemplateAnalysisStatus,
    TemplateFramework,
)


try:
    from app.services.template_blueprint import BlueprintBuilder
except ImportError:
    try:
        from app.modules.templates.blueprint import BlueprintBuilder
    except ImportError:

        class BlueprintBuilder:
            def save_to_template(
                self,
                template: Any,
                directory: Path,
                db: Any = None,
            ) -> dict[str, Any]:
                raise RuntimeError(
                    "BlueprintBuilder is not configured"
                )


def get_storage_paths() -> dict[str, Path]:
    storage_root = Path(
        os.getenv(
            "WORKFORCE_STORAGE_ROOT",
            "storage",
        )
    )

    return {
        "templates": storage_root / "templates",
        "uploads": storage_root / "uploads",
    }


def _http_error(
    status_code: int,
    detail: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )


def _is_symbolic_link(
    info: zipfile.ZipInfo,
) -> bool:
    unix_mode = info.external_attr >> 16
    return stat.S_ISLNK(unix_mode)


def _normalise_member_name(
    name: str,
) -> str:
    return name.replace("\\", "/")


def _inspect_archive(
    zip_path: Path,
) -> list[tuple[zipfile.ZipInfo, PurePosixPath]]:
    zip_path = Path(zip_path)

    if not zip_path.is_file():
        raise _http_error(
            400,
            "Stored file is not a valid ZIP archive.",
        )

    inspected: list[
        tuple[zipfile.ZipInfo, PurePosixPath]
    ] = []

    maximum_uncompressed_size = 256 * 1024 * 1024
    maximum_compression_ratio = 1000
    total_uncompressed_size = 0

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            for info in archive.infolist():
                name = _normalise_member_name(info.filename)

                if not name or "\x00" in name:
                    raise _http_error(
                        400,
                        "ZIP contains an unsafe empty or invalid path.",
                    )

                if _is_symbolic_link(info):
                    raise _http_error(
                        400,
                        "ZIP contains a symbolic-link entry.",
                    )

                if name.startswith("/"):
                    raise _http_error(
                        400,
                        "ZIP contains an absolute path.",
                    )

                if len(name) >= 2 and name[1] == ":":
                    raise _http_error(
                        400,
                        "ZIP contains a Windows drive-qualified path.",
                    )

                # Validate raw components before path normalization.
                member_name = (
                    name[:-1]
                    if info.is_dir() and name.endswith("/")
                    else name
                )

                parts = member_name.split("/")

                if any(
                    part in {"", ".", ".."} or ":" in part
                    for part in parts
                ):
                    raise _http_error(
                        400,
                        "ZIP contains an unsafe traversal path.",
                    )

                # Preserve ZIP forward slashes on Windows.
                relative = PurePosixPath(*parts)

                if not info.is_dir():
                    total_uncompressed_size += max(
                        info.file_size,
                        0,
                    )

                    if (
                        total_uncompressed_size
                        > maximum_uncompressed_size
                    ):
                        raise _http_error(
                            400,
                            "ZIP exceeds the maximum uncompressed size.",
                        )

                    compression_ratio = (
                        info.file_size
                        / max(info.compress_size, 1)
                    )

                    if (
                        compression_ratio
                        > maximum_compression_ratio
                    ):
                        raise _http_error(
                            400,
                            "ZIP contains an unsafe compression ratio.",
                        )

                inspected.append((info, relative))

    except (zipfile.BadZipFile, OSError) as exc:
        raise _http_error(
            400,
            "Uploaded file must be a valid ZIP archive.",
        ) from exc

    if not inspected:
        raise _http_error(
            400,
            "ZIP archive is empty.",
        )

    return inspected


def _safe_extract(
    zip_path: Path,
    destination: Path,
) -> None:
    zip_path = Path(zip_path)
    destination = Path(destination)

    inspected = _inspect_archive(zip_path)

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination_root = destination.resolve()

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            for info, relative in inspected:
                target = destination.joinpath(*relative.parts)
                resolved_target = target.resolve()

                try:
                    resolved_target.relative_to(destination_root)
                except ValueError as exc:
                    raise _http_error(
                        400,
                        "ZIP contains an unsafe path outside the destination.",
                    ) from exc

                if info.is_dir():
                    target.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    continue

                target.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with archive.open(info, "r") as source:
                    with target.open("wb") as output:
                        shutil.copyfileobj(source, output)

    except HTTPException:
        raise
    except (zipfile.BadZipFile, OSError) as exc:
        raise _http_error(
            400,
            "ZIP archive could not be safely extracted.",
        ) from exc


def _framework_from_blueprint(
    blueprint: dict[str, Any],
) -> TemplateFramework:
    raw_framework = (
        blueprint.get("framework")
        or blueprint.get("template_dna", {}).get("framework")
    )

    if raw_framework is None:
        raise ValueError(
            "Blueprint does not define a framework."
        )

    framework_key = str(raw_framework).strip().lower()

    framework_map = {
        "static_html": TemplateFramework.STATIC_HTML,
        "html": TemplateFramework.STATIC_HTML,
        "php": TemplateFramework.PHP,
        "react": TemplateFramework.REACT,
        "next": TemplateFramework.NEXT,
        "tailwind": TemplateFramework.TAILWIND,
    }

    try:
        return framework_map[framework_key]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported template framework: {raw_framework}"
        ) from exc


def _analysis_report(
    template: Any,
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    existing_report = getattr(
        template,
        "analysis_report",
        None,
    )

    report = dict(existing_report or {})

    report.update(
        {
            "status": "analyzed",
            "framework": (
                _framework_from_blueprint(blueprint).value
            ),
            "homepage_file": getattr(
                template,
                "homepage_file",
                None,
            ),
            "quality_score": getattr(
                template,
                "quality_score",
                0.0,
            ),
        }
    )

    for key in (
        "engine",
        "version",
        "security",
        "visual",
        "recommendation",
    ):
        if key in blueprint:
            report[key] = blueprint[key]

    return report


def _run_analysis(
    db: Any,
    template: Any,
) -> None:
    source_zip_path = getattr(
        template,
        "source_zip_path",
        None,
    )

    if not source_zip_path:
        raise _http_error(
            400,
            "Template has no stored archive path.",
        )

    zip_path = Path(source_zip_path)

    if not zip_path.is_file():
        raise _http_error(
            409,
            "Stored template archive is missing.",
        )

    storage_paths = get_storage_paths()
    templates_root = Path(storage_paths["templates"])
    destination = templates_root / str(template.id)

    try:
        if destination.exists():
            shutil.rmtree(destination)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        _safe_extract(zip_path, destination)

        template.extracted_path = str(destination)

        if hasattr(db, "flush"):
            db.flush()

        builder = BlueprintBuilder()

        blueprint = builder.save_to_template(
            template,
            destination,
            db=db,
        )

        if blueprint is None:
            blueprint = getattr(
                template,
                "blueprint",
                None,
            )

        if not isinstance(blueprint, dict):
            raise RuntimeError(
                "BlueprintBuilder returned an invalid blueprint."
            )

        template.blueprint = blueprint
        template.framework = _framework_from_blueprint(
            blueprint
        )
        template.analysis_report = _analysis_report(
            template,
            blueprint,
        )
        template.analysis_status = (
            TemplateAnalysisStatus.ANALYZED
        )

        if hasattr(db, "flush"):
            db.flush()

    except HTTPException:
        if destination.exists():
            shutil.rmtree(
                destination,
                ignore_errors=True,
            )
        raise

    except Exception as exc:
        template.analysis_status = (
            TemplateAnalysisStatus.FAILED
        )
        template.analysis_report = {
            "status": "failed",
            "error": str(exc),
        }

        if hasattr(db, "flush"):
            db.flush()

        if destination.exists():
            shutil.rmtree(
                destination,
                ignore_errors=True,
            )

        raise _http_error(
            422,
            f"Template analysis failed: {exc}",
        ) from exc


__all__ = [
    "BlueprintBuilder",
    "get_storage_paths",
    "_inspect_archive",
    "_safe_extract",
    "_framework_from_blueprint",
    "_run_analysis",
]