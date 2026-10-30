from __future__ import annotations

import csv
import io
import json

from collections.abc import (
    Iterator,
)

from app.modules.reports.schemas import (
    ReportRunResponse,
)


def _scalar_text(
    value,
) -> str:
    if value is None:
        return ""

    if isinstance(
        value,
        bool,
    ):
        return (
            "true"
            if value
            else "false"
        )

    if isinstance(
        value,
        (
            str,
            int,
            float,
        ),
    ):
        return str(
            value
        )

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
    )


def flatten_report_data(
    value,
    *,
    path: str = "data",
) -> Iterator[
    tuple[
        str,
        str,
    ]
]:
    if isinstance(
        value,
        dict,
    ):
        if not value:
            yield (
                path,
                "{}",
            )
            return

        for key, item in (
            value.items()
        ):
            child = (
                f"{path}.{key}"
            )

            yield from (
                flatten_report_data(
                    item,
                    path=child,
                )
            )

        return

    if isinstance(
        value,
        list,
    ):
        if not value:
            yield (
                path,
                "[]",
            )
            return

        for index, item in (
            enumerate(
                value
            )
        ):
            child = (
                f"{path}[{index}]"
            )

            yield from (
                flatten_report_data(
                    item,
                    path=child,
                )
            )

        return

    yield (
        path,
        _scalar_text(
            value
        ),
    )


def report_to_csv(
    report: ReportRunResponse,
) -> str:
    buffer = io.StringIO(
        newline=""
    )

    writer = csv.writer(
        buffer
    )

    writer.writerow(
        [
            "path",
            "value",
        ]
    )

    metadata = {
        "workspace_id": str(
            report.workspace_id
        ),
        "report": (
            report.report.value
        ),
        "scope": (
            report.scope.value
        ),
        "generated_at": (
            report.generated_at
            .isoformat()
        ),
        "parameters": (
            report.parameters
            .model_dump(
                mode="json"
            )
        ),
    }

    for (
        path,
        value,
    ) in flatten_report_data(
        metadata,
        path="meta",
    ):
        writer.writerow(
            [
                path,
                value,
            ]
        )

    for (
        path,
        value,
    ) in flatten_report_data(
        report.data,
        path="data",
    ):
        writer.writerow(
            [
                path,
                value,
            ]
        )

    return buffer.getvalue()


def report_filename(
    report: ReportRunResponse,
) -> str:
    stamp = (
        report.generated_at
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    return (
        "workforceos_"
        f"{report.report.value}_"
        f"{stamp}.csv"
    )


__all__ = [
    "flatten_report_data",
    "report_to_csv",
    "report_filename",
]