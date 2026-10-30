import asyncio
import unittest
from pathlib import Path
import importlib.util

path = Path(__file__).resolve().parents[1] / 'patch/backend/app/modules/live_monitoring/native_frame_relay.py'
spec = importlib.util.spec_from_file_location('native_frame_relay', path)
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

JPEG = b'\xff\xd8' + b'frame' + b'\xff\xd9'

class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.r = mod.NativeFrameRelay()
        self.pub, self.view = await self.r.issue(workspace_id='w1', session_id='s1', employee_id='e1', device_id='d1')

    async def test_consent_and_video(self):
        with self.assertRaises(mod.RelayError):
            await self.r.publish(session_id='s1',workspace_id='w1',publisher_token=self.pub,jpeg=JPEG)
        await self.r.approve(session_id='s1',workspace_id='w1',publisher_token=self.pub)
        self.assertEqual(1,await self.r.publish(session_id='s1',workspace_id='w1',publisher_token=self.pub,jpeg=JPEG))
        self.assertEqual((1,JPEG),await self.r.snapshot(session_id='s1',workspace_id='w1',viewer_token=self.view))

    async def test_workspace_isolation(self):
        with self.assertRaises(mod.RelayError):
            await self.r.snapshot(session_id='s1',workspace_id='w2',viewer_token=self.view)

    async def test_wrong_role_and_revocation(self):
        with self.assertRaises(mod.RelayError):
            await self.r.approve(session_id='s1',workspace_id='w1',publisher_token=self.view)
        await self.r.revoke(session_id='s1',workspace_id='w1')
        with self.assertRaises(mod.RelayError):
            await self.r.snapshot(session_id='s1',workspace_id='w1',viewer_token=self.view)

    async def test_invalid_frame(self):
        await self.r.approve(session_id='s1',workspace_id='w1',publisher_token=self.pub)
        with self.assertRaises(mod.RelayError):
            await self.r.publish(session_id='s1',workspace_id='w1',publisher_token=self.pub,jpeg=b'not-a-jpeg')

    async def test_duplicate_session(self):
        with self.assertRaises(mod.RelayError):
            await self.r.issue(workspace_id='w1',session_id='s1',employee_id='e1',device_id='d1')

    async def test_expiry(self):
        self.r._leases['s1'].expiry = 0
        with self.assertRaises(mod.RelayError):
            await self.r.snapshot(session_id='s1',workspace_id='w1',viewer_token=self.view)
        await self.r.purge()
        self.assertEqual({},self.r._leases)

if __name__ == '__main__': unittest.main()
