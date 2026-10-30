import asyncio
import importlib.util
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv)>1 else Path('backend/app/modules/live_monitoring/native_frame_relay.py')
spec = importlib.util.spec_from_file_location('native_frame_relay_under_test',path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

async def main():
    relay=module.NativeFrameRelay()
    p, v=await relay.issue(workspace_id='w',session_id='s',employee_id='e',device_id='d',expires_in=30)
    await relay.approve(session_id='s',workspace_id='w',publisher_token=p)
    for i in range(5):
        await relay.publish(session_id='s',workspace_id='w',publisher_token=p,jpeg=b'\xff\xd8\x00\xff\xd9')
    seq,_=await relay.snapshot(session_id='s',workspace_id='w',viewer_token=v,after=0)
    assert seq==5,seq
    relay._leases['s'].expiry=0  # deterministic lease expiry without sleeping
    p2,v2=await relay.issue(workspace_id='w',session_id='s',employee_id='e',device_id='d',expires_in=30)
    await relay.approve(session_id='s',workspace_id='w',publisher_token=p2)
    await relay.publish(session_id='s',workspace_id='w',publisher_token=p2,jpeg=b'\xff\xd8\x00\xff\xd9')
    seq2,frame=await relay.snapshot(session_id='s',workspace_id='w',viewer_token=v2,after=seq)
    assert seq2==6 and frame, (seq2,frame)
    print('PASS: frame sequence continues across lease renewal (5 -> 6)')

asyncio.run(main())
