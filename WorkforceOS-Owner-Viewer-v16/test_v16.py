import pathlib
import tempfile
import shutil
import subprocess
import sys
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path('/mnt/data/sim-v15b')
RELS=['backend/app/modules/live_monitoring/router.py','apps/web/app/(workspace)/monitoring/live-screen/page.tsx']
with tempfile.TemporaryDirectory() as d:
  root=pathlib.Path(d)
  for rel in RELS:
    p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(SOURCE/rel,p)
  cmd=[sys.executable,str(ROOT/'patch_v16.py'),'--root',str(root)]
  subprocess.run(cmd,check=True)
  subprocess.run(cmd+['--apply'],check=True)
  subprocess.run([sys.executable,'-m','py_compile',str(root/RELS[0])],check=True)
  backend=(root/RELS[0]).read_text(); page=(root/RELS[1]).read_text()
  assert backend.index('@router.get("/current-session")') < backend.index('"/live-sessions/{session_id}"')
  for security in ['requested_by_user_id == access.actor_user_id','can_access_employee','expires_at > now']:
    assert security in backend,security
  assert 'NativeSessionFrameViewer' in page
  assert 'current-session' in page
  assert 'requestLiveSession(' not in page
  assert 'autoRequestKeyRef' not in page
  subprocess.run(cmd+['--apply'],check=True)
print('V16 regression smoke PASS')
