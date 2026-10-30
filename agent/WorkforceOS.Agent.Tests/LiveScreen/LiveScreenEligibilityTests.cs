using WorkforceOS.Agent.LiveScreen;

namespace WorkforceOS.Agent.Tests.LiveScreen;

public sealed class LiveScreenEligibilityTests
{
    private static LiveScreenContext Valid() => new()
    {
        EmployeeId = Guid.NewGuid(),
        DeviceId = Guid.NewGuid(),
        WorkspaceId = Guid.NewGuid(),
        IsAuthenticated = true,
        RoleAllowsSharing = true,
        EmployeeOptedIn = true,
        IsShiftActive = true,
        IsSessionAuthorized = true,
        IsMonitoringIndicatorVisible = true,
        CanEmployeeStopSharing = true
    };

    [Fact]
    public void AuthorizedContextAllowsSharing()
    {
        Assert.True(LiveScreenEligibility.Evaluate(Valid()).CanShare);
    }

    [Theory]
    [InlineData("role")]
    [InlineData("consent")]
    [InlineData("shift")]
    [InlineData("session")]
    [InlineData("indicator")]
    [InlineData("stop_control")]
    [InlineData("employee_stop")]
    [InlineData("logout")]
    [InlineData("auth")]
    [InlineData("identity")]
    public void MissingSafetyRequirementBlocksSharing(string caseName)
    {
        var context = Valid();
        context = caseName switch
        {
            "role" => context with { RoleAllowsSharing = false },
            "consent" => context with { EmployeeOptedIn = false },
            "shift" => context with { IsShiftActive = false },
            "session" => context with { IsSessionAuthorized = false },
            "indicator" => context with { IsMonitoringIndicatorVisible = false },
            "stop_control" => context with { CanEmployeeStopSharing = false },
            "employee_stop" => context with { EmployeeRequestedStop = true },
            "logout" => context with { LogoutRequested = true },
            "auth" => context with { IsAuthenticated = false },
            "identity" => context with { DeviceId = Guid.Empty },
            _ => throw new ArgumentOutOfRangeException(nameof(caseName))
        };
        Assert.False(LiveScreenEligibility.Evaluate(context).CanShare);
    }
}
