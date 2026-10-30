from app.main import app

print("APPLICATION ROUTES")

for index, route in enumerate(app.routes):
    print(
        index,
        "TYPE=", type(route).__name__,
        "PATH=", getattr(route, "path", None),
        "NAME=", getattr(route, "name", None),
        "NESTED_COUNT=", len(getattr(route, "routes", []) or []),
    )
