using System.IO.Pipes;
using System.Security.Principal;

namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingPipeClient
{
    private readonly ILogger<AppTrackingPipeClient> _logger;

    public AppTrackingPipeClient(
        ILogger<AppTrackingPipeClient> logger)
    {
        _logger =
            logger;
    }

    public async Task SendAsync(
        AppTrackingSessionObservation observation,
        TimeSpan timeout,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(
            observation);

        observation.Validate();

        using CancellationTokenSource timeoutSource =
            CancellationTokenSource.CreateLinkedTokenSource(
                cancellationToken);

        timeoutSource.CancelAfter(
            timeout);

        await using NamedPipeClientStream pipe =
            new(
                serverName: ".",
                pipeName:
                    AppTrackingPipeNames.PipeName,
                direction:
                    PipeDirection.Out,
                options:
                    PipeOptions.Asynchronous,
                impersonationLevel:
                    TokenImpersonationLevel.Impersonation);

        try
        {
            await pipe.ConnectAsync(
                timeoutSource.Token);

            if (!pipe.IsConnected)
            {
                throw new IOException(
                    "AppTracking named-pipe connection was not established.");
            }

            await AppTrackingPipeProtocol.WriteAsync(
                pipe,
                observation,
                timeoutSource.Token);

            _logger.LogDebug(
                "Sent AppTracking observation. Session={SessionId}, Process={ProcessName}.",
                observation.SessionId,
                observation.ProcessName);
        }
        catch (OperationCanceledException)
            when (
                timeoutSource.IsCancellationRequested
                && !cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException(
                $"Timed out sending AppTracking observation after {timeout.TotalSeconds:0.#} seconds.");
        }
    }
}