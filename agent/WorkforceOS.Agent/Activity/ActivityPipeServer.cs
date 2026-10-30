using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivityPipeServer
{
    private readonly ActivityObservationValidator _validator;
    private readonly ILogger<ActivityPipeServer> _logger;

    public ActivityPipeServer(
        ActivityObservationValidator validator,
        ILogger<ActivityPipeServer> logger)
    {
        _validator = validator;
        _logger = logger;
    }

    public async Task<ActivitySessionObservation> ReceiveAsync(
        CancellationToken cancellationToken)
    {
        await using NamedPipeServerStream pipe =
            CreatePipe();

        _logger.LogDebug(
            "Waiting for WorkforceOS activity helper connection on pipe {PipeName}.",
            ActivityPipeNames.PipeName);

        await pipe.WaitForConnectionAsync(
            cancellationToken);

        _logger.LogDebug(
            "WorkforceOS activity helper connected.");

        try
        {
            ActivitySessionObservation observation =
                await ActivityPipeProtocol.ReadAsync(
                    pipe,
                    cancellationToken);

            string connectedUserSid =
                GetConnectedClientSid(
                    pipe);

            _validator.Validate(
                observation,
                connectedUserSid);

            _logger.LogDebug(
                "Accepted WorkforceOS activity observation. Session={SessionId}, UserSid={UserSid}, State={State}, IdleSeconds={IdleSeconds}.",
                observation.SessionId,
                connectedUserSid,
                observation.State,
                observation.IdleSeconds);

            return observation;
        }
        catch (OperationCanceledException)
            when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception exception)
        {
            _logger.LogError(
                exception,
                "Failed to receive or validate WorkforceOS activity pipe observation.");

            throw;
        }
    }

    private static NamedPipeServerStream CreatePipe()
    {
        PipeSecurity security =
            new();

        SecurityIdentifier localSystemSid =
            new(
                WellKnownSidType.LocalSystemSid,
                null);

        SecurityIdentifier administratorsSid =
            new(
                WellKnownSidType.BuiltinAdministratorsSid,
                null);

        SecurityIdentifier interactiveSid =
            new(
                WellKnownSidType.InteractiveSid,
                null);

        SecurityIdentifier networkSid =
            new(
                WellKnownSidType.NetworkSid,
                null);

        security.SetAccessRuleProtection(
            isProtected: true,
            preserveInheritance: false);

        security.AddAccessRule(
            new PipeAccessRule(
                localSystemSid,
                PipeAccessRights.FullControl,
                AccessControlType.Allow));

        security.AddAccessRule(
            new PipeAccessRule(
                administratorsSid,
                PipeAccessRights.FullControl,
                AccessControlType.Allow));

        security.AddAccessRule(
            new PipeAccessRule(
                interactiveSid,
                PipeAccessRights.ReadWrite |
                PipeAccessRights.Synchronize,
                AccessControlType.Allow));

        security.AddAccessRule(
            new PipeAccessRule(
                networkSid,
                PipeAccessRights.FullControl,
                AccessControlType.Deny));

        return NamedPipeServerStreamAcl.Create(
            pipeName: ActivityPipeNames.PipeName,
            direction: PipeDirection.In,
            maxNumberOfServerInstances: 1,
            transmissionMode: PipeTransmissionMode.Byte,
            options: PipeOptions.Asynchronous,
            inBufferSize: 16 * 1024,
            outBufferSize: 0,
            pipeSecurity: security,
            inheritability: HandleInheritability.None,
            additionalAccessRights: (PipeAccessRights)0);
    }

    private static string GetConnectedClientSid(
        NamedPipeServerStream pipe)
    {
        if (!pipe.IsConnected)
        {
            throw new IOException(
                "Activity named-pipe client disconnected before identity validation.");
        }

        string? connectedSid =
            null;

        pipe.RunAsClient(
            () =>
            {
                using WindowsIdentity identity =
                    WindowsIdentity.GetCurrent(
                        TokenAccessLevels.Query);

                connectedSid =
                    identity.User?.Value;
            });

        if (string.IsNullOrWhiteSpace(
            connectedSid))
        {
            throw new UnauthorizedAccessException(
                "Unable to resolve Windows SID for connected activity helper.");
        }

        return connectedSid;
    }
}