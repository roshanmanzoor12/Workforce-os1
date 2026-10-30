using System.IO.Pipes;
using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivityPipeClient
{
    private readonly ILogger<ActivityPipeClient>
        _logger;

    public ActivityPipeClient(
        ILogger<ActivityPipeClient> logger
    )
    {
        _logger =
            logger;
    }

    public async Task SendAsync(
        ActivitySessionObservation observation,
        TimeSpan timeout,
        CancellationToken cancellationToken = default
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        if (
            timeout
            <= TimeSpan.Zero
        )
        {
            throw new ArgumentOutOfRangeException(
                nameof(timeout),
                "Pipe connection timeout must be positive."
            );
        }

        observation.Validate();

        using CancellationTokenSource timeoutSource =
            CancellationTokenSource
                .CreateLinkedTokenSource(
                    cancellationToken
                );

        timeoutSource.CancelAfter(
            timeout
        );

        using NamedPipeClientStream pipe =
            new(
                ".",
                ActivityPipeNames.ServicePipeName,
                PipeDirection.Out,
                PipeOptions.Asynchronous
            );

        try
        {
            await pipe.ConnectAsync(
                timeoutSource.Token
            );

            await ActivityPipeProtocol
                .WriteAsync(
                    pipe,
                    observation,
                    timeoutSource.Token
                );

            _logger.LogDebug(
                "Activity observation sent to local WorkforceOS service. Session={SessionId}, State={State}, IdleSeconds={IdleSeconds}.",
                observation.SessionId,
                observation.State,
                observation.IdleSeconds
            );
        }
        catch (
            OperationCanceledException
        )
        when (
            !cancellationToken
                .IsCancellationRequested
        )
        {
            throw new TimeoutException(
                (
                    "Timed out connecting to WorkforceOS " +
                    "activity service pipe."
                )
            );
        }
    }
}