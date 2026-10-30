namespace WorkforceOS.Agent.LiveScreen;

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
    // Set from the backend session lease; change of session must restart transport.
    public Guid SessionId { get; init; }
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
