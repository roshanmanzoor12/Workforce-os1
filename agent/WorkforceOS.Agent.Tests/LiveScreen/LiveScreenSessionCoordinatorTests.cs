using WorkforceOS.Agent.LiveScreen;

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
