"""
Contract tests for the template upload / extraction / analysis pipeline.

Scope:

    stored ZIP
        ↓
    _inspect_archive
        ↓
    _safe_extract
        ↓
    _run_analysis
        ↓
    BlueprintBuilder.save_to_template
        ↓
    Template analysis status

No external AI provider is used.

No real database is required.

These tests verify that the production template upload layer:

- accepts normal website ZIP archives;
- rejects invalid ZIP files;
- rejects zip-slip traversal paths;
- rejects absolute paths;
- rejects Windows drive-qualified paths;
- rejects symbolic-link entries;
- rejects unsafe compression ratios;
- safely extracts files inside the intended directory;
- preserves extracted file bytes;
- maps BlueprintBuilder framework output to TemplateFramework;
- marks successful analysis as ANALYZED;
- marks failed analysis as FAILED;
- removes partially extracted trees after failure;
- never reports analysis success when the stored source archive is missing.
"""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

import app.api.templates as templates_module
from app.models.template import (
    TemplateAnalysisStatus,
    TemplateFramework,
)


# =====================================================================
# Fake database session
# =====================================================================


class _FakeDb:
    def __init__(
        self,
    ) -> None:
        self.added: list[Any] = []
        self.flush_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0

    def add(
        self,
        value: Any,
    ) -> None:
        self.added.append(
            value
        )

    def flush(
        self,
    ) -> None:
        self.flush_count += 1

    def commit(
        self,
    ) -> None:
        self.commit_count += 1

    def rollback(
        self,
    ) -> None:
        self.rollback_count += 1

    def refresh(
        self,
        value: Any,
    ) -> None:
        _ = value
        self.refresh_count += 1


# =====================================================================
# Template record
# =====================================================================


def _template_record(
    zip_path: Path,
) -> SimpleNamespace:
    return SimpleNamespace(
        id="template-upload-test-1",

        source_zip_path=str(
            zip_path
        ),

        extracted_path=None,

        framework=None,

        homepage_file=None,

        blueprint={},

        pages=[],

        assets={},

        color_palette=[],

        seo_metadata={},

        analysis_report={},

        quality_score=0.0,

        analysis_status=(
            TemplateAnalysisStatus.PENDING
        ),
    )


# =====================================================================
# ZIP helpers
# =====================================================================


def _create_valid_zip(
    root: Path,
) -> Path:
    zip_path = (
        root
        / "template.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "index.html",
            """<!doctype html>
<html>
<head>
    <title>Upload Pipeline</title>
    <link rel="stylesheet" href="assets/css/theme.css">
</head>
<body>
    <main>
        <h1>Upload Pipeline</h1>
    </main>
    <script src="assets/js/main.js"></script>
</body>
</html>
""",
        )

        archive.writestr(
            "about.html",
            """<!doctype html>
<html>
<head>
    <title>About</title>
</head>
<body>
    <main>
        <h1>About</h1>
    </main>
</body>
</html>
""",
        )

        archive.writestr(
            "assets/css/theme.css",
            "body{margin:0;font-family:Inter,sans-serif}",
        )

        archive.writestr(
            "assets/js/main.js",
            "window.templateReady=true;",
        )

        archive.writestr(
            "assets/images/hero.bin",
            b"\x00UPLOAD_PIPELINE_IMAGE\x01",
        )

    return zip_path


def _create_zip_with_member(
    root: Path,
    member_name: str,
    content: bytes | str = b"unsafe",
) -> Path:
    zip_path = (
        root
        / "unsafe.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            member_name,
            content,
        )

    return zip_path


# =====================================================================
# Valid archive
# =====================================================================


def test_valid_template_zip_passes_archive_inspection(
    tmp_path: Path,
) -> None:
    zip_path = (
        _create_valid_zip(
            tmp_path
        )
    )

    inspected = (
        templates_module
        ._inspect_archive(
            zip_path
        )
    )

    assert isinstance(
        inspected,
        list,
    )

    assert inspected

    names = {
        str(
            relative
        )
        for _info, relative
        in inspected
    }

    assert (
        "index.html"
        in names
    )

    assert (
        "about.html"
        in names
    )

    assert (
        "assets/css/theme.css"
        in names
    )

    assert (
        "assets/js/main.js"
        in names
    )


# =====================================================================
# Invalid ZIP
# =====================================================================


def test_invalid_zip_is_rejected(
    tmp_path: Path,
) -> None:
    invalid = (
        tmp_path
        / "invalid.zip"
    )

    invalid.write_bytes(
        b"this is not a zip archive"
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._inspect_archive(
            invalid
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert (
        "valid ZIP"
        in str(
            exc_info.value.detail
        )
        or "ZIP"
        in str(
            exc_info.value.detail
        )
    )


# =====================================================================
# Zip-slip traversal
# =====================================================================


@pytest.mark.parametrize(
    "member_name",
    [
        "../outside.html",
        "assets/../../outside.js",
        "./index.html",
    ],
)
def test_relative_traversal_paths_are_rejected(
    tmp_path: Path,
    member_name: str,
) -> None:
    zip_path = (
        _create_zip_with_member(
            tmp_path,
            member_name,
        )
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._inspect_archive(
            zip_path
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert (
        "unsafe"
        in str(
            exc_info.value.detail
        ).lower()
        or "path"
        in str(
            exc_info.value.detail
        ).lower()
    )


# =====================================================================
# Absolute archive path
# =====================================================================


def test_absolute_archive_path_is_rejected(
    tmp_path: Path,
) -> None:
    zip_path = (
        _create_zip_with_member(
            tmp_path,
            "/etc/passwd",
        )
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._inspect_archive(
            zip_path
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert (
        "absolute"
        in str(
            exc_info.value.detail
        ).lower()
    )


# =====================================================================
# Windows drive path
# =====================================================================


def test_windows_drive_qualified_path_is_rejected(
    tmp_path: Path,
) -> None:
    zip_path = (
        _create_zip_with_member(
            tmp_path,
            "C:/Windows/System32/file.txt",
        )
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._inspect_archive(
            zip_path
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert (
        "drive"
        in str(
            exc_info.value.detail
        ).lower()
        or "unsafe"
        in str(
            exc_info.value.detail
        ).lower()
    )


# =====================================================================
# Symlink ZIP entry
# =====================================================================


def test_symbolic_link_entry_is_rejected(
    tmp_path: Path,
) -> None:
    zip_path = (
        tmp_path
        / "symlink.zip"
    )

    info = zipfile.ZipInfo(
        "linked-file"
    )

    #
    # Mark archive member as a Unix symbolic link.
    #

    info.create_system = 3

    info.external_attr = (
        (
            stat.S_IFLNK
            | 0o777
        )
        << 16
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
    ) as archive:
        archive.writestr(
            info,
            "../outside.txt",
        )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._inspect_archive(
            zip_path
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert (
        "symbolic"
        in str(
            exc_info.value.detail
        ).lower()
        or "symlink"
        in str(
            exc_info.value.detail
        ).lower()
    )


# =====================================================================
# Compression ratio
# =====================================================================


def test_extreme_compression_ratio_is_rejected(
    tmp_path: Path,
) -> None:
    zip_path = (
        tmp_path
        / "compression-bomb.zip"
    )

    highly_compressible = (
        b"A"
        * (
            2
            * 1024
            * 1024
        )
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        archive.writestr(
            "huge.txt",
            highly_compressible,
        )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._inspect_archive(
            zip_path
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert (
        "compression"
        in str(
            exc_info.value.detail
        ).lower()
    )


# =====================================================================
# Safe extraction
# =====================================================================


def test_safe_extract_creates_expected_template_tree(
    tmp_path: Path,
) -> None:
    zip_path = (
        _create_valid_zip(
            tmp_path
        )
    )

    destination = (
        tmp_path
        / "extracted"
    )

    templates_module._safe_extract(
        zip_path,
        destination,
    )

    assert (
        destination
        .joinpath(
            "index.html"
        )
        .is_file()
    )

    assert (
        destination
        .joinpath(
            "about.html"
        )
        .is_file()
    )

    assert (
        destination
        .joinpath(
            "assets",
            "css",
            "theme.css",
        )
        .is_file()
    )

    assert (
        destination
        .joinpath(
            "assets",
            "js",
            "main.js",
        )
        .is_file()
    )

    assert (
        destination
        .joinpath(
            "assets",
            "images",
            "hero.bin",
        )
        .is_file()
    )


# =====================================================================
# Extracted bytes
# =====================================================================


def test_safe_extract_preserves_file_bytes(
    tmp_path: Path,
) -> None:
    zip_path = (
        _create_valid_zip(
            tmp_path
        )
    )

    destination = (
        tmp_path
        / "extracted"
    )

    templates_module._safe_extract(
        zip_path,
        destination,
    )

    expected = (
        b"\x00UPLOAD_PIPELINE_IMAGE\x01"
    )

    actual = (
        destination
        .joinpath(
            "assets",
            "images",
            "hero.bin",
        )
        .read_bytes()
    )

    assert (
        actual
        == expected
    )


# =====================================================================
# Zip-slip must never escape destination
# =====================================================================


def test_safe_extract_never_writes_outside_destination(
    tmp_path: Path,
) -> None:
    zip_path = (
        _create_zip_with_member(
            tmp_path,
            "../escaped.txt",
            "escaped",
        )
    )

    destination = (
        tmp_path
        / "safe-root"
    )

    escaped = (
        tmp_path
        / "escaped.txt"
    )

    with pytest.raises(
        HTTPException
    ):
        templates_module._safe_extract(
            zip_path,
            destination,
        )

    assert not escaped.exists()


# =====================================================================
# Framework conversion
# =====================================================================


@pytest.mark.parametrize(
    (
        "framework",
        "expected",
    ),
    [
        (
            "static_html",
            TemplateFramework.STATIC_HTML,
        ),
        (
            "php",
            TemplateFramework.PHP,
        ),
        (
            "react",
            TemplateFramework.REACT,
        ),
        (
            "next",
            TemplateFramework.NEXT,
        ),
        (
            "tailwind",
            TemplateFramework.TAILWIND,
        ),
    ],
)
def test_framework_from_blueprint_maps_known_frameworks(
    framework: str,
    expected: TemplateFramework,
) -> None:
    result = (
        templates_module
        ._framework_from_blueprint(
            {
                "framework":
                    framework,
            }
        )
    )

    assert (
        result
        == expected
    )


# =====================================================================
# Invalid framework
# =====================================================================


def test_framework_from_blueprint_rejects_unknown_framework(
) -> None:
    with pytest.raises(
        Exception
    ) as exc_info:
        templates_module._framework_from_blueprint(
            {
                "framework":
                    "made_up_framework",
            }
        )

    assert (
        "unsupported"
        in str(
            exc_info.value
        ).lower()
        or "framework"
        in str(
            exc_info.value
        ).lower()
    )


# =====================================================================
# Controlled BlueprintBuilder
# =====================================================================


class _SuccessfulBlueprintBuilder:
    def save_to_template(
        self,
        template,
        directory: Path,
        db=None,
    ):
        _ = db

        directory = Path(
            directory
        )

        assert (
            directory
            .joinpath(
                "index.html"
            )
            .is_file()
        )

        blueprint = {
            "version":
                2,

            "engine":
                "blueprint_v2",

            "framework":
                "static_html",

            "homepage":
                "index.html",

            "seo_seed":
                {
                    "title":
                        "Upload Pipeline",
                },

            "template_dna":
                {
                    "framework":
                        "static_html",

                    "homepage":
                        "index.html",

                    "files":
                        {
                            "html":
                                [
                                    "index.html",
                                    "about.html",
                                ],

                            "css":
                                [
                                    "assets/css/theme.css",
                                ],

                            "js":
                                [
                                    "assets/js/main.js",
                                ],

                            "images":
                                [
                                    "assets/images/hero.bin",
                                ],
                        },
                },

            "editor":
                {
                    "document_model_version":
                        1,

                    "source":
                        "source_dom_v2",

                    "pages":
                        [
                            {
                                "path":
                                    "index.html",
                            },
                            {
                                "path":
                                    "about.html",
                            },
                        ],

                    "capabilities":
                        {
                            "element_selection":
                                True,

                            "text_editing":
                                True,

                            "source_tree":
                                True,

                            "visual_geometry":
                                False,
                        },

                    "supports":
                        {
                            "source_html":
                                True,

                            "browser_geometry":
                                False,
                        },
                },

            "security":
                {},

            "visual":
                {
                    "visual_geometry":
                        False,
                },

            "quality_score":
                85.0,

            "recommendation":
                "ready",
        }

        #
        # Mimic the already-tested BlueprintBuilder persistence contract.
        #

        template.blueprint = (
            blueprint
        )

        template.homepage_file = (
            "index.html"
        )

        template.quality_score = (
            85.0
        )

        template.pages = (
            blueprint[
                "editor"
            ][
                "pages"
            ]
        )

        template.assets = (
            blueprint[
                "template_dna"
            ][
                "files"
            ]
        )

        template.color_palette = [
            "#14532d",
        ]

        template.analysis_report = {
            "engine":
                "blueprint_v2",

            "version":
                2,

            "quality_score":
                85.0,

            "recommendation":
                "ready",

            "security":
                {},

            "visual":
                {
                    "visual_geometry":
                        False,
                },
        }

        return blueprint


class _BrokenBlueprintBuilder:
    def save_to_template(
        self,
        template,
        directory: Path,
        db=None,
    ):
        _ = template
        _ = directory
        _ = db

        raise RuntimeError(
            "forced blueprint failure"
        )


# =====================================================================
# Analysis success
# =====================================================================


def test_run_analysis_marks_template_analyzed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zip_path = (
        _create_valid_zip(
            tmp_path
        )
    )

    template = (
        _template_record(
            zip_path
        )
    )

    db = (
        _FakeDb()
    )

    storage_root = (
        tmp_path
        / "storage"
    )

    templates_dir = (
        storage_root
        / "templates"
    )

    uploads_dir = (
        storage_root
        / "uploads"
    )

    templates_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    uploads_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    monkeypatch.setattr(
        templates_module,
        "get_storage_paths",
        lambda: {
            "templates":
                templates_dir,

            "uploads":
                uploads_dir,
        },
    )

    monkeypatch.setattr(
        templates_module,
        "BlueprintBuilder",
        _SuccessfulBlueprintBuilder,
    )

    templates_module._run_analysis(
        db,
        template,
    )

    assert (
        template.analysis_status
        == TemplateAnalysisStatus.ANALYZED
    )

    assert (
        template.framework
        == TemplateFramework.STATIC_HTML
    )

    assert (
        template.homepage_file
        == "index.html"
    )

    assert (
        template.blueprint[
            "version"
        ]
        == 2
    )

    assert (
        template.blueprint[
            "engine"
        ]
        == "blueprint_v2"
    )

    assert (
        template.extracted_path
        is not None
    )

    extracted = Path(
        template.extracted_path
    )

    assert extracted.is_dir()

    assert (
        extracted
        .joinpath(
            "index.html"
        )
        .is_file()
    )

    assert (
        extracted
        .joinpath(
            "assets",
            "css",
            "theme.css",
        )
        .is_file()
    )

    assert (
        template.analysis_report[
            "status"
        ]
        == "analyzed"
    )

    assert (
        template.analysis_report[
            "framework"
        ]
        == "static_html"
    )

    assert (
        template.analysis_report[
            "homepage_file"
        ]
        == "index.html"
    )

    assert (
        db.flush_count
        >= 2
    )


# =====================================================================
# Analysis failure
# =====================================================================


def test_run_analysis_marks_template_failed_on_blueprint_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zip_path = (
        _create_valid_zip(
            tmp_path
        )
    )

    template = (
        _template_record(
            zip_path
        )
    )

    db = (
        _FakeDb()
    )

    templates_dir = (
        tmp_path
        / "templates"
    )

    templates_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    monkeypatch.setattr(
        templates_module,
        "get_storage_paths",
        lambda: {
            "templates":
                templates_dir,

            "uploads":
                (
                    tmp_path
                    / "uploads"
                ),
        },
    )

    monkeypatch.setattr(
        templates_module,
        "BlueprintBuilder",
        _BrokenBlueprintBuilder,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._run_analysis(
            db,
            template,
        )

    assert (
        exc_info.value.status_code
        == 422
    )

    assert (
        template.analysis_status
        == TemplateAnalysisStatus.FAILED
    )

    assert (
        template.analysis_report[
            "status"
        ]
        == "failed"
    )

    assert (
        "forced blueprint failure"
        in template.analysis_report[
            "error"
        ]
    )


# =====================================================================
# Failed analysis removes extracted tree
# =====================================================================


def test_failed_analysis_removes_partial_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zip_path = (
        _create_valid_zip(
            tmp_path
        )
    )

    template = (
        _template_record(
            zip_path
        )
    )

    db = (
        _FakeDb()
    )

    templates_dir = (
        tmp_path
        / "templates"
    )

    templates_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    monkeypatch.setattr(
        templates_module,
        "get_storage_paths",
        lambda: {
            "templates":
                templates_dir,

            "uploads":
                (
                    tmp_path
                    / "uploads"
                ),
        },
    )

    monkeypatch.setattr(
        templates_module,
        "BlueprintBuilder",
        _BrokenBlueprintBuilder,
    )

    expected_destination = (
        templates_dir
        / str(
            template.id
        )
    )

    with pytest.raises(
        HTTPException
    ):
        templates_module._run_analysis(
            db,
            template,
        )

    assert not (
        expected_destination.exists()
    )


# =====================================================================
# Missing stored archive
# =====================================================================


def test_run_analysis_rejects_missing_stored_archive(
    tmp_path: Path,
) -> None:
    missing = (
        tmp_path
        / "missing.zip"
    )

    template = (
        _template_record(
            missing
        )
    )

    db = (
        _FakeDb()
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._run_analysis(
            db,
            template,
        )

    assert (
        exc_info.value.status_code
        == 409
    )

    assert (
        "missing"
        in str(
            exc_info.value.detail
        ).lower()
    )


# =====================================================================
# Missing source path value
# =====================================================================


def test_run_analysis_rejects_template_without_source_zip(
) -> None:
    template = SimpleNamespace(
        id="template-no-source",

        source_zip_path=None,

        analysis_status=(
            TemplateAnalysisStatus.PENDING
        ),

        analysis_report={},
    )

    db = (
        _FakeDb()
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        templates_module._run_analysis(
            db,
            template,
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert (
        "no stored archive"
        in str(
            exc_info.value.detail
        ).lower()
    )