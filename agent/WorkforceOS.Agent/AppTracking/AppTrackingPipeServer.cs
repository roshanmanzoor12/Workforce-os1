using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;

namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingPipeServer
{
    private readonly AppTrackingObservationValidator _validator;

    private readonly ILogger<AppTrackingPipeServer> _logger;

    public AppTrackingPipeServer(
        AppTrackingObservationValidator validator,
        ILogger<AppTrackingPipeServer> logger)
    {
        _validator =
            validator;

        _logger =
            logger;
    }

    public async Task<AppTrackingSessionObservation> ReceiveAsync(
        CancellationToken cancellationToken)
    {
        await using NamedPipeServerStream pipe =
            CreatePipe();

        _logger.LogDebug(
            "Waiting for AppTracking helper on pipe {PipeName}.",
            AppTrackingPipeNames.PipeName);

        await pipe.WaitForConnectionAsync(
            cancellationToken);

        try
        {
            AppTrackingSessionObservation observation =
                await AppTrackingPipeProtocol.ReadAsync(
                    pipe,
                    cancellationToken);

            string connectedUserSid =
                GetConnectedClientSid(
                    pipe);

            _validator.Validate(
                observation,
                connectedUserSid);

            _logger.LogDebug(
                "Accepted AppTracking observation. Session={SessionId}, SID={UserSid}, Process={ProcessName}.",
                observation.SessionId,
                connectedUserSid,
                observation.ProcessName);

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
                "Failed to receive AppTracking observation.");

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
            pipeName:
                AppTrackingPipeNames.PipeName,

            direction:
                PipeDirection.In,

            maxNumberOfServerInstances:
                1,

            transmissionMode:
                PipeTransmissionMode.Byte,

            options:
                PipeOptions.Asynchronous,

            inBufferSize:
                AppTrackingPipeNames.MaximumMessageBytes,

            outBufferSize:
                0,

            pipeSecurity:
                security,

            inheritability:
                HandleInheritability.None,

            additionalAccessRights:
                (PipeAccessRights)0);
    }

    private static string GetConnectedClientSid(
        NamedPipeServerStream pipe)
    {
        if (!pipe.IsConnected)
        {
            throw new IOException(
                "AppTracking helper disconnected before identity validation.");
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
                "Unable to resolve AppTracking helper Windows SID.");
        }

        return connectedSid;
    }
}