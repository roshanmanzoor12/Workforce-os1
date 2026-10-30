#!/usr/bin/env python3
"""Add a tested, fail-closed LIVE SCREEN eligibility policy to WorkforceOS.Agent.
Does not implement recording, screen capture, streaming, or automatically start capture.
"""
from pathlib import Path
from datetime import datetime
import shutil, sys

root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os').resolve()
agent=root/'agent'/'WorkforceOS.Agent'
tests=root/'agent'/'WorkforceOS.Agent.Tests'
for p in (agent/'WorkforceOS.Agent.csproj', tests/'WorkforceOS.Agent.Tests.csproj'):
    if not p.exists(): raise SystemExit(f'Project missing: {p}')

files={
agent/'LiveScreen'/'LiveScreenEligibility.cs':r'''namespace WorkforceOS.Agent.LiveScreen;

/// <summary>
/// Decision gate for an employee-visible, user-controllable live screen session.
/// The backend must authenticate employee/device/workspace, sign all inputs,
/// and enforce viewer authorization separately. This class NEVER starts capture.
/// </summary>
public static class LiveScreenEligibility
{
    public static LiveScreenDecision Evaluate(LiveScreenContext context)
    {
        ArgumentNullException.ThrowIfNull(context);

        if (context.EmployeeId == Guid.Empty || context.DeviceId == Guid.Empty ||
            context.WorkspaceId == Guid.Empty)
            return LiveScreenDecision.Deny("missing_identity");

        if (!context.IsAuthenticated)
            return LiveScreenDecision.Deny("not_authenticated");

        if (!context.RoleAllowsSharing)
            return LiveScreenDecision.Deny("role_permission_disabled");

        if (!context.EmployeeOptedIn)
            return LiveScreenDecision.Deny("consent_missing_or_revoked");

        if (!context.IsShiftActive)
            return LiveScreenDecision.Deny("shift_inactive");

        if (!context.IsSessionAuthorized)
            return LiveScreenDecision.Deny("server_session_not_authorized");

        if (!context.IsMonitoringIndicatorVisible)
            return LiveScreenDecision.Deny("indicator_not_visible");

        if (!context.CanEmployeeStopSharing)
            return LiveScreenDecision.Deny("stop_control_unavailable");

        if (context.EmployeeRequestedStop)
            return LiveScreenDecision.Deny("employee_stopped");

        if (context.LogoutRequested)
            return LiveScreenDecision.Deny("logout");

        return LiveScreenDecision.Allow();
    }
}

public sealed record LiveScreenContext
{
    public Guid EmployeeId { get; init; }
    public Guid DeviceId { get; init; }
    public Guid WorkspaceId { get; init; }
    public bool IsAuthenticated { get; init; }
    public bool RoleAllowsSharing { get; init; }
    public bool EmployeeOptedIn { get; init; }
    public bool IsShiftActive { get; init; }
    public bool IsSessionAuthorized { get; init; }
    public bool IsMonitoringIndicatorVisible { get; init; }
    public bool CanEmployeeStopSharing { get; init; }
    public bool EmployeeRequestedStop { get; init; }
    public bool LogoutRequested { get; init; }
}

public sealed record LiveScreenDecision(bool CanShare, string Reason)
{
    public static LiveScreenDecision Allow() => new(true, "authorized");
    public static LiveScreenDecision Deny(string reason) => new(false, reason);
}
''',
tests/'LiveScreen'/'LiveScreenEligibilityTests.cs':r'''using WorkforceOS.Agent.LiveScreen;

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
'''
}
backup=root/'backups'/('agent-live-policy-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
for dest, content in files.items():
    if dest.exists():
        rel=dest.relative_to(root); bp=backup/rel
        bp.parent.mkdir(parents=True, exist_ok=True);shutil.copy2(dest,bp)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content,encoding='utf-8')
    print('INSTALLED',dest)
print('BACKUP',backup if backup.exists() else '(new files only)')
print('IMPORTANT: Policy/tests only. Does not start screen capture or stream video.')
print('NEXT: dotnet test agent\\WorkforceOS.Agent.Tests\\WorkforceOS.Agent.Tests.csproj')
