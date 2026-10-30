from app.main import app

print("=" * 70)
print("ALL APP ROUTES ENDING IN /ws")
print("=" * 70)

found = False

for route in app.routes:
    path = getattr(route, "path", None)

    if path and path.endswith("/ws"):
        found = True
        print(
            type(route).__name__,
            path,
        )

print("")
print("FOUND_WS_SUFFIX:", found)
