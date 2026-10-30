from __future__ import annotations

import json
import struct
import subprocess
import sys
import time
from pathlib import Path


NATIVE_HOST_EXE = Path(
    r"C:\workforce-os\artifacts\website-native-host"
    r"\WorkforceOS.WebsiteNativeHost.exe"
)

TEST_MESSAGE = {
    "protocolVersion": 1,
    "browserProcessName": "chrome.exe",
    "domain": "github.com",
    "pageUrl": None,
    "pageTitle": None,
    "observedAt": None,
}


def write_native_message(
    process: subprocess.Popen[bytes],
    message: dict,
) -> None:
    body = json.dumps(
        message,
        separators=(",", ":"),
    ).encode("utf-8")

    header = struct.pack(
        "<I",
        len(body),
    )

    if process.stdin is None:
        raise RuntimeError(
            "Native host stdin is unavailable."
        )

    process.stdin.write(
        header
    )

    process.stdin.write(
        body
    )

    process.stdin.flush()


def read_exact(
    stream,
    size: int,
) -> bytes:
    data = bytearray()

    while len(data) < size:
        chunk = stream.read(
            size - len(data)
        )

        if not chunk:
            break

        data.extend(
            chunk
        )

    return bytes(
        data
    )


def read_native_message(
    process: subprocess.Popen[bytes],
) -> dict:
    if process.stdout is None:
        raise RuntimeError(
            "Native host stdout is unavailable."
        )

    header = read_exact(
        process.stdout,
        4,
    )

    if len(header) != 4:
        raise RuntimeError(
            "Native host returned no framed response."
        )

    payload_length = struct.unpack(
        "<I",
        header,
    )[0]

    if payload_length <= 0:
        raise RuntimeError(
            "Native host returned invalid payload length."
        )

    payload = read_exact(
        process.stdout,
        payload_length,
    )

    if len(payload) != payload_length:
        raise RuntimeError(
            "Native host response was incomplete."
        )

    return json.loads(
        payload.decode(
            "utf-8"
        )
    )


def main() -> int:
    if not NATIVE_HOST_EXE.exists():
        raise RuntimeError(
            f"Native host executable missing: "
            f"{NATIVE_HOST_EXE}"
        )

    message = dict(
        TEST_MESSAGE
    )

    message[
        "observedAt"
    ] = (
        time.strftime(
            "%Y-%m-%dT%H:%M:%S",
            time.gmtime(),
        )
        + "Z"
    )

    print(
        f"Native host: {NATIVE_HOST_EXE}"
    )

    print(
        "Launching native host..."
    )

    process = subprocess.Popen(
        [
            str(
                NATIVE_HOST_EXE
            )
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        print(
            "Sending privacy-safe github.com test observation..."
        )

        write_native_message(
            process,
            message,
        )

        response = read_native_message(
            process
        )

        print(
            "Native host response:"
        )

        print(
            json.dumps(
                response,
                indent=2,
            )
        )

        if (
            response.get(
                "accepted"
            )
            is not True
        ):
            raise RuntimeError(
                "Native host rejected the observation: "
                + str(
                    response
                )
            )

        print(
            "PASS native host accepted observation"
        )

        return 0

    finally:
        try:
            if process.stdin is not None:
                process.stdin.close()
        except Exception:
            pass

        try:
            process.wait(
                timeout=5
            )
        except subprocess.TimeoutExpired:
            process.kill()

        if (
            process.returncode
            not in (
                None,
                0,
            )
        ):
            stderr = b""

            if process.stderr is not None:
                stderr = (
                    process.stderr.read()
                )

            if stderr:
                sys.stderr.write(
                    stderr.decode(
                        "utf-8",
                        errors="replace",
                    )
                )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )