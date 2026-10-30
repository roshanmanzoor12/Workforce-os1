from app.modules.channels.realtime_router import router

print("ROUTER_TYPE:", type(router).__name__)

for route in router.routes:
    print(
        "TYPE=", type(route).__name__,
        "PATH=", getattr(route, "path", None),
        "METHODS=", getattr(route, "methods", None),
        "ENDPOINT=", getattr(
            getattr(route, "endpoint", None),
            "__name__",
            None,
        ),
    )
