using System.IO.Pipes;
using System.Security.AccessControl;
using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingPipeServer
{
    private const int ListenerCount =
        4;

    private readonly
        WebsiteTrackingPipeConnectionHandler
        _connectionHandler;

    private readonly
        WebsiteTrackingPipeDiagnostics
        _diagnostics;

    private readonly
        ILogger<
            WebsiteTrackingPipeServer
        >
        _logger;

    public WebsiteTrackingPipeServer(
        WebsiteTrackingPipeConnectionHandler connectionHandler,
        WebsiteTrackingPipeDiagnostics diagnostics,
        ILogger<
            WebsiteTrackingPipeServer
        > logger
    )
    {
        _connectionHandler =
            connectionHandler;

        _diagnostics =
            diagnostics;

        _logger =
            logger;
    }

    public async Task RunAsync(
        CancellationToken cancellationToken
    )
    {
        Task[] listeners =
            Enumerable
                .Range(
                    0,
                    ListenerCount
                )
                .Select(
                    listenerId =>
                        RunListenerAsync(
                            listenerId,
                            cancellationToken
                        )
                )
                .ToArray();

        await Task.WhenAll(
            listeners
        );
    }

    private async Task RunListenerAsync(
        int listenerId,
        CancellationToken cancellationToken
    )
    {
        while (
            !cancellationToken
                .IsCancellationRequested
        )
        {
            try
            {
                await using NamedPipeServerStream pipe =
                    CreateServer();

                await pipe.WaitForConnectionAsync(
                    cancellationToken
                );

                await _connectionHandler
                    .HandleAsync(
                        pipe,
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
                break;
            }
            catch (
                Exception exception
            )
            {
                _diagnostics
                    .RecordConnectionFailure();

                _logger.LogWarning(
                    exception,
                    "Website Tracking pipe listener {ListenerId} failed.",
                    listenerId
                );

                try
                {
                    await Task.Delay(
                        TimeSpan.FromSeconds(5),
                        cancellationToken
                    );
                }
                catch (
                    OperationCanceledException
                )
                {
                    break;
                }
            }
        }
    }

    private static NamedPipeServerStream
        CreateServer()
    {
        PipeSecurity security =
            WebsiteTrackingPipeSecurity
                .Create();

        return NamedPipeServerStreamAcl.Create(
            pipeName:
                WebsiteTrackingPipeNames
                    .ObservationPipe,

            direction:
                PipeDirection.InOut,

            maxNumberOfServerInstances:
                ListenerCount,

            transmissionMode:
                PipeTransmissionMode.Byte,

            options:
                PipeOptions.Asynchronous,

            inBufferSize:
                WebsiteTrackingPipeNames
                    .MaximumMessageBytes,

            outBufferSize:
                WebsiteTrackingPipeNames
                    .MaximumMessageBytes,

            pipeSecurity:
                security
        );
    }
}