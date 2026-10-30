import ast
import pathlib
import sys
import unittest

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
import patch_sources as patch

OLD = pathlib.Path('/mnt/data/current_source')  # optional fixture in dev environment

class PatchContracts(unittest.TestCase):
    def test_device_auto_accept_requires_real_companion_indicator(self):
        sample = '''var decision = inbox.ConsentGranted
                                ? "accept"
                                : await CompanionRequestNotifier.RequestDecisionAsync(
                                    item.SessionId, item.ExpiresAt, stoppingToken);'''
        changed = patch.agent_worker_patch(sample)
        self.assertIn('PrepareIndicatorAsync', changed)
        self.assertIn('prepared ? "accept"', changed)
        self.assertNotIn('inbox.ConsentGranted\n                                ? "accept"', changed)

    def test_already_prompting_v14_branch_supported(self):
        sample = '''var decision = await CompanionRequestNotifier.RequestDecisionAsync(
                                item.SessionId, item.ExpiresAt, stoppingToken);'''
        changed = patch.agent_worker_patch(sample)
        self.assertIn('PrepareIndicatorAsync', changed)

    def test_unknown_agent_source_fails_closed(self):
        with self.assertRaises(patch.SourceConflict):
            patch.agent_worker_patch('var decision = "accept";')

    def test_native_router_contains_terminal_rejection(self):
        source = (PACKAGE / 'files/backend/app/modules/live_monitoring/auto_lease.py').read_text()
        self.assertIn("state='ended'", source)
        self.assertIn('120', source)
        ast.parse(source)

    def test_session_root_has_rotation_guard(self):
        src = (PACKAGE / 'files/backend/app/modules/live_monitoring/auto_flow_router.py').read_text()
        for marker in ('replaced_by_session_id', 'revoked_at', 'owner_access(', 'live_screen_saved_approvals', 'revoke_sessions(', 'multiple_online_devices_require_selection'):
            self.assertIn(marker, src)
        ast.parse(src)

    def test_migration_is_tenant_scoped(self):
        schema=(PACKAGE/'migration.sql').read_text()
        self.assertIn('last_ping_at', schema)
        self.assertIn('live_screen_saved_approvals', schema)
        self.assertIn('BEGIN;', schema)
        self.assertIn('COMMIT;', schema)

if __name__ == '__main__': unittest.main()
