from __future__ import annotations

import importlib

import fastapi


def main() -> None:
    main_module = importlib.import_module("app.main")
    voice_module = importlib.import_module(
        "app.modules.voice_channels.router"
    )

    app = main_module.app
    router = voice_module.router

    print("FASTAPI VERSION:", fastapi.__version__)
    print("MAIN FILE:", main_module.__file__)
    print("VOICE ROUTER FILE:", voice_module.__file__)
    print("VOICE ROUTER PREFIX:", router.prefix)

    print("\nVOICE ROUTER INTERNAL ROUTES:")

    internal_count = 0

    for route in router.routes:
        path = getattr(route, "path", None)

        if path is None:
            print(
                "INTERNAL WRAPPER:",
                type(route).__name__,
            )
            continue

        internal_count += 1

        print(
            sorted(getattr(route, "methods", None) or []),
            path,
        )

    print("INTERNAL PATH COUNT:", internal_count)

    print("\nAPP TOP-LEVEL ROUTE TYPES:")

    route_types: dict[str, int] = {}

    for route in app.routes:
        name = type(route).__name__
        route_types[name] = route_types.get(name, 0) + 1

    for name, count in sorted(route_types.items()):
        print(name, count)

    print("\nVOICE ROUTES IN OPENAPI:")

    try:
        schema = app.openapi()
    except Exception:
        print("OPENAPI GENERATION FAILED:")
        raise

    paths = schema.get("paths", {})

    voice_paths = {
        path: operations
        for path, operations in paths.items()
        if "voice" in path.lower()
    }

    http_methods = {
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "options",
        "head",
        "trace",
    }

    for path, operations in sorted(voice_paths.items()):
        methods = sorted(
            method.upper()
            for method in operations
            if method.lower() in http_methods
        )

        print(methods, path)

    print("OPENAPI VOICE PATH COUNT:", len(voice_paths))

    if voice_paths:
        print(
            "\nRESULT: Voice HTTP endpoints appear in OpenAPI. "
            "Request handling and permissions still need testing."
        )
    elif internal_count:
        print(
            "\nRESULT: The voice router contains endpoints, "
            "but they do not appear in the app OpenAPI schema."
        )
    else:
        print(
            "\nRESULT: No direct endpoint paths were found "
            "in the imported voice router."
        )


if __name__ == "__main__":
    main()