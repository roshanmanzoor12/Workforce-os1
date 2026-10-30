import app.main
import app.modules.notifications.router as notification_router

print("MAIN FILE:")
print(app.main.__file__)

print("NOTIFICATION ROUTER FILE:")
print(notification_router.__file__)

print("ROUTER INTERNAL ROUTES:")
for route in notification_router.router.routes:
    print(
        sorted(getattr(route, "methods", [])),
        route.path,
    )

print("APP ROUTES:")
for route in app.main.app.routes:
    if "notification" in getattr(route, "path", "").lower():
        print(
            sorted(getattr(route, "methods", [])),
            route.path,
        )
