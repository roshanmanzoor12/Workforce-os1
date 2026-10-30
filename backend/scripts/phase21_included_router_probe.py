from app.main import app

for route in app.routes:
    if type(route).__name__ == "_IncludedRouter":
        print("TYPE:", type(route).__name__)
        print("ATTRIBUTES:")
        print(
            sorted(
                name
                for name in dir(route)
                if not name.startswith("__")
            )
        )
        print("OBJECT DICT:")
        print(getattr(route, "__dict__", {}))
        break
