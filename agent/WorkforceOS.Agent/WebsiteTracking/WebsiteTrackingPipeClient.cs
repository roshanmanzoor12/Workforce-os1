using System.IO.Pipes;
using System.Security.Principal;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingPipeClient
{
    private const int MaximumAttempts =
        8;

    private static readonly TimeSpan
        ConnectionTimeout =
            TimeSpan.FromSeconds(
                3
            );

    public async Task<
        WebsiteTrackingPipeAck
    > SendAsync(
        WebsiteTrackingObservation observation,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        Exception? lastException =
            null;

        for (
            int attempt = 1;
            attempt <= MaximumAttempts;
            attempt++
        )
        {
            cancellationToken
                .ThrowIfCancellationRequested();

            try
            {
                return await SendOnceAsync(
                    observation,
                    cancellationToken
                );
            }
            catch (
                OperationCanceledException
            )
            when (
                cancellationToken
                    .IsCancellationRequested
            )
            {
                throw;
            }
            catch (
                Exception exception
            )
            {
                lastException =
                    exception;

                if (
                    attempt >= MaximumAttempts
                )
                {
                    throw new WebsiteTrackingPipeConnectionException(
                        "Website Tracking Agent pipe remained unavailable.",
                        lastException,
                        attempt
                    );
                }

                int delayMilliseconds =
                    150
                    + (
                        attempt
                        * 150
                    );

                await Task.Delay(
                    TimeSpan.FromMilliseconds(
                        delayMilliseconds
                    ),
                    cancellationToken
                );
            }
        }

        throw new WebsiteTrackingPipeConnectionException(
            "Website Tracking Agent pipe connection failed.",
            lastException,
            MaximumAttempts
        );
    }

    private static async Task<
        WebsiteTrackingPipeAck
    > SendOnceAsync(
        WebsiteTrackingObservation observation,
        CancellationToken cancellationToken
    )
    {
        using CancellationTokenSource timeout =
            CancellationTokenSource
                .CreateLinkedTokenSource(
                    cancellationToken
                );

        timeout.CancelAfter(
            ConnectionTimeout
        );

        await using NamedPipeClientStream pipe =
            new(
                serverName: ".",
                pipeName:
                    WebsiteTrackingPipeNames
                        .ObservationPipe,
                direction:
                    PipeDirection.InOut,
                options:
                    PipeOptions.Asynchronous,
                impersonationLevel:
                    TokenImpersonationLevel
                        .Impersonation
            );

        await pipe.ConnectAsync(
            timeout.Token
        );

        await WebsiteTrackingPipeMessageFraming
            .WriteObservationAsync(
                pipe,
                observation,
                timeout.Token
            );

        return await WebsiteTrackingPipeMessageFraming
            .ReadAckAsync(
                pipe,
                timeout.Token
            );
    }
}