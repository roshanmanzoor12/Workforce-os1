from __future__ import annotations

import json
import struct
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


NATIVE_HOST = Path(
    r"C:\workforce-os\artifacts\website-native-host"
    r"\WorkforceOS.WebsiteNativeHost.exe"
)

DOMAINS = [
    "github.com",
    "youtube.com",
    "github.com",
    "youtube.com",
    "github.com",
]


def write_message(
    process: subprocess.Popen[bytes],
    message: dict,
) -> None:
    if process.stdin is None:
        raise RuntimeError(
            "stdin unavailable"
        )

    payload = json.dumps(
        message,
        separators=(",", ":"),
    ).encode("utf-8")

    process.stdin.write(
        struct.pack(
            "<I",
            len(payload),
        )
    )

    process.stdin.write(
        payload
    )

    process.stdin.flush()


def read_exact(
    stream,
    count: int,
) -> bytes:
    result = bytearray()

    while len(result) < count:
        block = stream.read(
            count - len(result)
        )

        if not block:
            break

        result.extend(
            block
        )

    return bytes(
        result
    )


def read_message(
    process: subprocess.Popen[bytes],
) -> dict:
    if process.stdout is None:
        raise RuntimeError(
            "stdout unavailable"
        )

    header = read_exact(
        process.stdout,
        4,
    )

    if len(header) != 4:
        raise RuntimeError(
            "No native-host response header."
        )

    length = struct.unpack(
        "<I",
        header,
    )[0]

    payload = read_exact(
        process.stdout,
        length,
    )

    if len(payload) != length:
        raise RuntimeError(
            "Incomplete native-host response."
        )

    return json.loads(
        payload.decode("utf-8")
    )


def main() -> None:
    if not NATIVE_HOST.exists():
        raise RuntimeError(
            f"Native host missing: {NATIVE_HOST}"
        )

    accepted = 0

    for index, domain in enumerate(
        DOMAINS,
        start=1,
    ):
        process = subprocess.Popen(
            [
                str(NATIVE_HOST)
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            message = {
                "protocolVersion": 1,
                "browserProcessName": "chrome.exe",
                "domain": domain,
                "pageUrl": None,
                "pageTitle": None,
                "observedAt": (
                    datetime.now(
                        timezone.utc
                    )
                    .isoformat()
                ),
            }

            write_message(
                process,
                message,
            )

            response = read_message(
                process
            )

            print(
                f"{index}: {response}"
            )

            if (
                response.get("accepted")
                is not True
            ):
                raise RuntimeError(
                    f"Stress observation {index} rejected: "
                    f"{response}"
                )

            accepted += 1

        finally:
            if process.stdin is not None:
                process.stdin.close()

            try:
                process.wait(
                    timeout=5
                )
            except subprocess.TimeoutExpired:
                process.kill()

        time.sleep(
            0.15
        )

    if accepted != len(DOMAINS):
        raise RuntimeError(
            "Not all stress observations were accepted."
        )

    print(
        f"PASS persistent pipe stress: {accepted}"
    )


if __name__ == "__main__":
    main()