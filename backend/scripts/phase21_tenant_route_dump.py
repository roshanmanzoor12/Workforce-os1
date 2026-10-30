from app.modules.tenant_api.router import router

print("TENANT ROUTER ROUTES")

for index, route in enumerate(router.routes):
    print(
        index,
        "TYPE=", type(route).__name__,
        "PATH=", getattr(route, "path", None),
        "NAME=", getattr(route, "name", None),
    )
