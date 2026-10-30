import sys, unittest, asyncio, pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1] / "patch" / "backend"))
from app.modules.live_monitoring.native_http_gateway import publish, snapshot, revoke

class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_snapshot_revoke(self):
        pic=b"\xff\xd8"+b"frame"+b"\xff\xd9"
        seq=await publish("ws","unique-a","emp","dev",20,pic)
        self.assertEqual(seq,1)
        value,back=await snapshot("ws","unique-a","emp","dev",20)
        self.assertEqual((value,back),(1,pic))
        await revoke("ws","unique-a")
        value,back=await snapshot("ws","unique-a","emp","dev",20)
        self.assertIsNone(back)
    async def test_invalid_jpeg(self):
        from app.modules.live_monitoring.native_frame_relay import RelayError
        with self.assertRaises(RelayError):
            await publish("ws","unique-b","emp","dev",20,b"not jpeg")
if __name__=="__main__": unittest.main()
