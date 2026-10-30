def require_permission(name:str):
    async def dep(): return None
    return dep
