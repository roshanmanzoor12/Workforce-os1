from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import DisciplinaryIncident
class DisciplineRepository:
    def __init__(self, session: AsyncSession): self.session=session
    async def add(self,value): self.session.add(value); await self.session.flush(); return value
    async def list(self, employee_id=None):
        q=select(DisciplinaryIncident).order_by(DisciplinaryIncident.created_at.desc())
        if employee_id is not None: q=q.where(DisciplinaryIncident.employee_id==employee_id)
        return list((await self.session.scalars(q)).all())
