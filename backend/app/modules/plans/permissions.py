PLANS_READ_PERMISSION = "plans.read"
PLANS_MANAGE_PERMISSION = "plans.manage"


def require_plans_read() -> bool:
    return True


def require_plans_manage() -> bool:
    return True