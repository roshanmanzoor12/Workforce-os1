#!/usr/bin/env python3
"""Workforce OS - guard against stale/switching live session IDs. Safe additive patch."""
from pathlib import Path
from datetime import datetime
import shutil, sys

root = Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
ctx = root/'agent/WorkforceOS.Agent/LiveScreen/LiveScreenEligibility.cs'
coord = root/'agent/WorkforceOS.Agent/LiveScreen/LiveScreenSessionCoordinator.cs'
tests = root/'agent/WorkforceOS.Agent.Tests/LiveScreen/LiveScreenSessionIdentityTests.cs'
for p in (ctx,coord):
    if not p.is_file(): raise SystemExit(f'Missing file: {p}')
a,b = ctx.read_text(encoding='utf-8-sig'),coord.read_text(encoding='utf-8-sig')
if 'SessionId { get; init; }' in a or '_sessionId' in b:
    raise SystemExit('Patch already installed or related changes detected. No files modified.')
assert 'public Guid WorkspaceId { get; init; }' in a
assert 'private Guid _workspaceId;' in b
assert '_workspaceId == context.WorkspaceId)' in b
assert '_workspaceId = context.WorkspaceId;' in b
assert '_employeeId = _deviceId = _workspaceId = Guid.Empty;' in b
assert not tests.exists(),f'Test file already exists: {tests}'
# Session ID optional for existing coordinator callers. When supplied, a changed session forces stop/restart.
a=a.replace('    public Guid WorkspaceId { get; init; }','    public Guid WorkspaceId { get; init; }\n    // Set from the backend session lease; change of session must restart transport.\n    public Guid SessionId { get; init; }')
b=b.replace('    private Guid _workspaceId;', '    private Guid _workspaceId;\n    private Guid _sessionId;')
b=b.replace('_deviceId == context.DeviceId && _workspaceId == context.WorkspaceId)', '_deviceId == context.DeviceId && _workspaceId == context.WorkspaceId &&\n                _sessionId == context.SessionId)')
b=b.replace('            _workspaceId = context.WorkspaceId;', '            _workspaceId = context.WorkspaceId;\n            _sessionId = context.SessionId;')
b=b.replace('_employeeId = _deviceId = _workspaceId = Guid.Empty;', '_employeeId = _deviceId = _workspaceId = _sessionId = Guid.Empty;')
test_text='''using WorkforceOS.Agent.LiveScreen;

namespace WorkforceOS.Agent.Tests.LiveScreen;

public sealed class LiveScreenSessionIdentityTests
{
    private sealed class Transport : ILiveScreenSessionTransport
    {
        public int Starts { get; private set; }
        public int Stops { get; private set; }
        public Task StartAsync(LiveScreenContext context, CancellationToken token)
        {
            Starts++;
            return Task.CompletedTask;
        }
        public Task StopAsync(CancellationToken token)
        {
            Stops++;
            return Task.CompletedTask;
        }
    }

    private static LiveScreenContext Authorized(Guid id) => new()
    {
        EmployeeId = Guid.NewGuid(), DeviceId = Guid.NewGuid(),
        WorkspaceId = Guid.NewGuid(), SessionId = id,
        IsAuthenticated = true, RoleAllowsSharing = true,
        EmployeeOptedIn = true, IsShiftActive = true,
        IsSessionAuthorized = true, IsMonitoringIndicatorVisible = true,
        CanEmployeeStopSharing = true
    };

    [Fact]
    public async Task RenewedSameSessionDoesNotRestart()
    {
        var transport = new Transport();
        await using var coordinator = new LiveScreenSessionCoordinator(transport);
        var input = Authorized(Guid.NewGuid());
        await coordinator.ReconcileAsync(input);
        await coordinator.ReconcileAsync(input);
        Assert.Equal(1, transport.Starts);
        Assert.Equal(0, transport.Stops);
    }

    [Fact]
    public async Task ReplacedServerSessionStopsPriorTransport()
    {
        var transport = new Transport();
        await using var coordinator = new LiveScreenSessionCoordinator(transport);
        var input = Authorized(Guid.NewGuid());
        await coordinator.ReconcileAsync(input);
        await coordinator.ReconcileAsync(input with { SessionId = Guid.NewGuid() });
        Assert.Equal(2, transport.Starts);
        Assert.Equal(1, transport.Stops);
    }

    [Fact]
    public async Task PermissionRevocationStopsSession()
    {
        var transport = new Transport();
        await using var coordinator = new LiveScreenSessionCoordinator(transport);
        var input = Authorized(Guid.NewGuid());
        await coordinator.ReconcileAsync(input);
        var decision = await coordinator.ReconcileAsync(input with { RoleAllowsSharing = false });
        Assert.False(decision.CanShare);
        Assert.Equal(1, transport.Stops);
    }
}
'''
backup = root/'backups'/f'live-session-identity-{datetime.now():%Y%m%d-%H%M%S}'
for p in (ctx,coord):
    dest=backup/p.relative_to(root)
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest)
ctx.write_text(a,encoding='utf-8')
coord.write_text(b,encoding='utf-8')
tests.parent.mkdir(parents=True,exist_ok=True)
tests.write_text(test_text,encoding='utf-8')
print('PATCHED',ctx)
print('PATCHED',coord)
print('ADDED',tests)
print('BACKUP',backup)
print('NOTE: Session identity guard only; no live video or production authorization integration.')
