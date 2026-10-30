using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;

namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingPipeSecurity
{
    public static PipeSecurity Create()
    {
        PipeSecurity security =
            new();

        security.SetAccessRuleProtection(
            isProtected:
                true,

            preserveInheritance:
                false
        );

        SecurityIdentifier localSystemSid =
            new(
                WellKnownSidType.LocalSystemSid,
                null
            );

        SecurityIdentifier administratorsSid =
            new(
                WellKnownSidType.BuiltinAdministratorsSid,
                null
            );

        SecurityIdentifier authenticatedUsersSid =
            new(
                WellKnownSidType.AuthenticatedUserSid,
                null
            );

        SecurityIdentifier networkSid =
            new(
                WellKnownSidType.NetworkSid,
                null
            );

        SecurityIdentifier anonymousSid =
            new(
                WellKnownSidType.AnonymousSid,
                null
            );

        security.AddAccessRule(
            new PipeAccessRule(
                localSystemSid,
                PipeAccessRights.FullControl,
                AccessControlType.Allow
            )
        );

        security.AddAccessRule(
            new PipeAccessRule(
                administratorsSid,
                PipeAccessRights.FullControl,
                AccessControlType.Allow
            )
        );

        /*
         * Local authenticated Windows users may use
         * the disclosed browser native-messaging bridge.
         *
         * InOut is required because the Agent returns
         * an acceptance ACK to the native host.
         */
        security.AddAccessRule(
            new PipeAccessRule(
                authenticatedUsersSid,
                PipeAccessRights.ReadWrite,
                AccessControlType.Allow
            )
        );

        /*
         * Explicitly reject remote/network and anonymous
         * identities at the Windows ACL layer.
         */
        security.AddAccessRule(
            new PipeAccessRule(
                networkSid,
                PipeAccessRights.FullControl,
                AccessControlType.Deny
            )
        );

        security.AddAccessRule(
            new PipeAccessRule(
                anonymousSid,
                PipeAccessRights.FullControl,
                AccessControlType.Deny
            )
        );

        return security;
    }

    public static bool IsAllowedLocalClient(
        NamedPipeServerStream pipe
    )
    {
        ArgumentNullException.ThrowIfNull(
            pipe
        );

        /*
         * Authorization is intentionally enforced by
         * the named-pipe ACL itself.
         *
         * A connection reaching this point has already
         * passed Windows access control:
         *
         *   LocalSystem        -> allowed
         *   Administrators     -> allowed
         *   AuthenticatedUser  -> allowed
         *   Network            -> denied
         *   Anonymous          -> denied
         *
         * Performing a second impersonation-token check
         * here caused valid Chromium Native Messaging
         * hosts and even direct native-host probes to be
         * rejected because browser/restricted tokens do
         * not always expose a usable impersonation
         * identity through RunAsClient() or
         * GetImpersonationUserName().
         */
        return pipe.IsConnected;
    }
}