from app.main import app

print("=" * 70)
print("REGISTERED WEBSOCKET ROUTES")
print("=" * 70)

found = False

for route in app.routes:
    path = getattr(route, "path", None)
    route_type = type(route).__name__

    if (
        path
        and (
            "realtime" in path.lower()
            or "channel" in path.lower()
            or "ws" in path.lower()
        )
    ):
        print(f"{route_type:30} {path}")

        if (
            "WebSocket" in route_type
            or path.endswith("/ws")
        ):
            found = True

print("")
print("WEBSOCKET_FOUND:", found)
