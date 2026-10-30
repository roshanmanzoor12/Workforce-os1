#!/usr/bin/env python3
"""Install testable live-screen session lifecycle coordinator. No screen capture."""
from pathlib import Path
import sys,shutil,datetime
root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os').resolve()
a=root/'agent'/'WorkforceOS.Agent'/'LiveScreen'
t=root/'agent'/'WorkforceOS.Agent.Tests'/'LiveScreen'
if not (a/'LiveScreenEligibility.cs').is_file():
    raise SystemExit('LiveScreenEligibility.cs not found; install previous policy patch first')
if not (root/'agent'/'WorkforceOS.Agent.Tests'/'WorkforceOS.Agent.Tests.csproj').is_file():
    raise SystemExit('Agent test project missing')
files={
a/'LiveScreenSessionCoordinator.cs':'''using System.Threading;

namespace WorkforceOS.Agent.LiveScreen;

/// <summary>
/// Manages an employee-visible live sharing session, but does not capture any pixels.
/// A production transport must enforce device identity and server-issued session grants.
/// Call ReconcileAsync on every authorization/shift change, and StopAsync on shutdown.
/// </summary>
public sealed class LiveScreenSessionCoordinator : IAsyncDisposable
{
    private readonly ILiveScreenSessionTransport _transport;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private bool _running;
    private bool _disposed;
    private Guid _employeeId;
    private Guid _deviceId;
    private Guid _workspaceId;

    public LiveScreenSessionCoordinator(ILiveScreenSessionTransport transport)
    {
        _transport = transport ?? throw new ArgumentNullException(nameof(transport));
    }

    public async Task<LiveScreenDecision> ReconcileAsync(
        LiveScreenContext context, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(context);
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            var decision = LiveScreenEligibility.Evaluate(context);
            if (!decision.CanShare)
            {
                await StopInternalAsync(cancellationToken).ConfigureAwait(false);
                return decision;
            }

            if (_running && _employeeId == context.EmployeeId &&
                _deviceId == context.DeviceId && _workspaceId == context.WorkspaceId)
                return decision; // Already active; do not duplicate a session.

            await StopInternalAsync(cancellationToken).ConfigureAwait(false);
            await _transport.StartAsync(context, cancellationToken).ConfigureAwait(false);
            _running = true;
            _employeeId = context.EmployeeId;
            _deviceId = context.DeviceId;
            _workspaceId = context.WorkspaceId;
            return decision;
        }
        finally { _gate.Release(); }
    }

    public async Task StopAsync(CancellationToken cancellationToken = default)
    {
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (_disposed) return;
            await StopInternalAsync(cancellationToken).ConfigureAwait(false);
        }
        finally { _gate.Release(); }
    }

    private async Task StopInternalAsync(CancellationToken cancellationToken)
    {
        if (!_running) return;
        // Fail closed: clear local state even if the downstream stop fails.
        _running = false;
        _employeeId = _deviceId = _workspaceId = Guid.Empty;
        await _transport.StopAsync(cancellationToken).ConfigureAwait(false);
    }

    public async ValueTask DisposeAsync()
    {
        await _gate.WaitAsync().ConfigureAwait(false);
        try
        {
            if (_disposed) return;
            try { await StopInternalAsync(CancellationToken.None).ConfigureAwait(false); }
            finally { _disposed = true; }
        }
        finally { _gate.Release(); }
        // Semaphore not disposed: allows harmless late cancellation/cleanup attempts.
    }
}

public interface ILiveScreenSessionTransport
{
    Task StartAsync(LiveScreenContext context, CancellationToken cancellationToken);
    Task StopAsync(CancellationToken cancellationToken);
}
''',
t/'LiveScreenSessionCoordinatorTests.cs':'''using WorkforceOS.Agent.LiveScreen;

namespace WorkforceOS.Agent.Tests.LiveScreen;

public sealed class LiveScreenSessionCoordinatorTests
{
    private sealed class FakeTransport : ILiveScreenSessionTransport
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

    private static LiveScreenContext Authorized() => new()
    {
        EmployeeId = Guid.NewGuid(), DeviceId = Guid.NewGuid(),
        WorkspaceId = Guid.NewGuid(), IsAuthenticated = true,
        RoleAllowsSharing = true, EmployeeOptedIn = true,
        IsShiftActive = true, IsSessionAuthorized = true,
        IsMonitoringIndicatorVisible = true, CanEmployeeStopSharing = true
    };

    [Fact]
    public async Task AuthorizedContextStartsOnce()
    {
        var fake = new FakeTransport();
        await using var coordinator = new LiveScreenSessionCoordinator(fake);
        var context = Authorized();
        Assert.True((await coordinator.ReconcileAsync(context)).CanShare);
        await coordinator.ReconcileAsync(context);
        Assert.Equal(1, fake.Starts);
    }

    [Fact]
    public async Task LogoutStopsSessionAndCannotRestartWithoutAuthorization()
    {
        var fake = new FakeTransport();
        await using var coordinator = new LiveScreenSessionCoordinator(fake);
        var context = Authorized();
        await coordinator.ReconcileAsync(context);
        Assert.False((await coordinator.ReconcileAsync(context with { LogoutRequested = true })).CanShare);
        Assert.Equal(1, fake.Stops);
        Assert.Equal(1, fake.Starts);
    }

    [Fact]
    public async Task RevokedConsentStopsAndExplicitNewAuthorizationCanRestart()
    {
        var fake = new FakeTransport();
        await using var coordinator = new LiveScreenSessionCoordinator(fake);
        var context = Authorized();
        await coordinator.ReconcileAsync(context);
        await coordinator.ReconcileAsync(context with { EmployeeOptedIn = false });
        Assert.Equal(1, fake.Stops);
        await coordinator.ReconcileAsync(context);
        Assert.Equal(2, fake.Starts);
    }

    [Fact]
    public async Task SwitchingWorkspaceStopsOldBeforeNewStart()
    {
        var fake = new FakeTransport();
        await using var coordinator = new LiveScreenSessionCoordinator(fake);
        var context = Authorized();
        await coordinator.ReconcileAsync(context);
        await coordinator.ReconcileAsync(context with { WorkspaceId = Guid.NewGuid() });
        Assert.Equal(2, fake.Starts);
        Assert.Equal(1, fake.Stops);
    }

    [Fact]
    public async Task InactiveShiftDoesNotStart()
    {
        var fake = new FakeTransport();
        await using var coordinator = new LiveScreenSessionCoordinator(fake);
        Assert.False((await coordinator.ReconcileAsync(Authorized() with { IsShiftActive = false })).CanShare);
        Assert.Equal(0, fake.Starts);
    }

    [Fact]
    public async Task DisposeEndsRunningSession()
    {
        var fake = new FakeTransport();
        var coordinator = new LiveScreenSessionCoordinator(fake);
        await coordinator.ReconcileAsync(Authorized());
        await coordinator.DisposeAsync();
        Assert.Equal(1, fake.Stops);
    }
}
'''}
backup=root/'backups'/('agent-live-runtime-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
for path,content in files.items():
    if path.exists():
        dst=backup/path.relative_to(root)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dst)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')
    print('INSTALLED',path)
print('BACKUP',backup if backup.exists() else '(new files only)')
print('NOTE: Runtime coordinator + tests only. No native capture, backend authorization fetch, transport, or automatic startup registered.')
