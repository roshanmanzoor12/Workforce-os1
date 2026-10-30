from pathlib import Path
import ast,sys,shutil,datetime
root=Path(sys.argv[1]); apply='--apply' in sys.argv[2:]
p=root/'backend/app/modules/live_monitoring/service.py'
text=p.read_text(encoding='utf-8-sig')
old='        now = self._now()\n        item = LiveScreenSession(\n            device_id=device.id,\n            employee_id=device.employee_id,\n            requested_by_user_id=access.actor_user_id,\n            status=LIVE_SESSION_STATUS_REQUESTED,\n'
new='        # Serialize requests for one DesktopAgentDevice, including concurrent\n        # requests from separate API workers. The DB lock is released at commit.\n        # Do not derive a requester identity from device credentials here.\n        await self.session.execute(\n            select(DesktopAgentDevice.id)\n            .where(DesktopAgentDevice.id == device.id)\n            .with_for_update()\n        )\n        now = self._now()\n        prior = await self.session.scalar(\n            select(LiveScreenSession)\n            .where(\n                LiveScreenSession.device_id == device.id,\n                LiveScreenSession.employee_id == device.employee_id,\n                LiveScreenSession.status.in_((\n                    LIVE_SESSION_STATUS_REQUESTED,\n                    LIVE_SESSION_STATUS_ACCEPTED,\n                    LIVE_SESSION_STATUS_ACTIVE,\n                )),\n                LiveScreenSession.expires_at > now,\n            )\n            .order_by(LiveScreenSession.created_at.desc())\n            .limit(1)\n        )\n        if prior is not None:\n            if prior.requested_by_user_id != access.actor_user_id:\n                raise LiveMonitoringPermissionError(\n                    "An active or pending request already exists for this device."\n                )\n            return self._live_response(prior)\n        item = LiveScreenSession(\n            device_id=device.id,\n            employee_id=device.employee_id,\n            requested_by_user_id=access.actor_user_id,\n            status=LIVE_SESSION_STATUS_REQUESTED,\n'
anchor='from sqlalchemy.ext.asyncio import (\n'
addition='from sqlalchemy import select\nfrom app.modules.desktop_agent.models import DesktopAgentDevice\n\n'
if new in text:
    print('ALREADY APPLIED: request deduplication');sys.exit(0)
if text.count(old)!=1 or text.count(anchor)!=1:
    raise SystemExit('PRECHECK FAILED: file differs from expected source; no modifications made')
updated=text.replace(old,new).replace(anchor,addition+anchor,1)
ast.parse(updated)
print('PREFLIGHT PASS: SQL row-locked idempotent owner request')
if not apply:
    print('DRY RUN ONLY. Use -Apply.');sys.exit(0)
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
backup=root/('WorkforceOS-v4-backup-'+stamp); dest=backup/'backend/app/modules/live_monitoring/service.py';dest.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(p,dest);p.write_text(updated,encoding='utf-8')
print('APPLIED: '+str(p));print('BACKUP: '+str(dest))
