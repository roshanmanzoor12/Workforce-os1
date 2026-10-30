using WorkforceOS.Agent.LiveScreen;

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
