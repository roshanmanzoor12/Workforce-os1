using System.Diagnostics;
using System.Security.Principal;

namespace WorkforceOS.Agent.Activity;

public sealed record ActivitySessionIdentity
{
    public required int SessionId
    {
        get;
        init;
    }

    public required string UserSid
    {
        get;
        init;
    }

    public static ActivitySessionIdentity Current()
    {
        using WindowsIdentity identity =
            WindowsIdentity.GetCurrent(
                TokenAccessLevels.Query
            );

        string? userSid =
            identity.User?.Value;

        if (
            string.IsNullOrWhiteSpace(
                userSid
            )
        )
        {
            throw new InvalidOperationException(
                "Unable to determine current Windows user SID."
            );
        }

        int sessionId =
            Process
                .GetCurrentProcess()
                .SessionId;

        return new ActivitySessionIdentity
        {
            SessionId =
                sessionId,

            UserSid =
                userSid
        };
    }
}