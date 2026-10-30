using System.IO.Pipes;
using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingPipeConnectionHandler
{
    private readonly
        WebsiteTrackingRuntimeCoordinator
        _coordinator;

    private readonly
        WebsiteTrackingObservationQueue
        _queue;

    private readonly
        WebsiteTrackingPipeDiagnostics
        _diagnostics;

    private readonly
        ILogger<
            WebsiteTrackingPipeConnectionHandler
        >
        _logger;

    public WebsiteTrackingPipeConnectionHandler(
        WebsiteTrackingRuntimeCoordinator coordinator,
        WebsiteTrackingObservationQueue queue,
        WebsiteTrackingPipeDiagnostics diagnostics,
        ILogger<
            WebsiteTrackingPipeConnectionHandler
        > logger
    )
    {
        _coordinator =
            coordinator;

        _queue =
            queue;

        _diagnostics =
            diagnostics;

        _logger =
            logger;
    }

    public async Task HandleAsync(
        NamedPipeServerStream pipe,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            pipe
        );

        if (
            !WebsiteTrackingPipeSecurity
                .IsAllowedLocalClient(
                    pipe
                )
        )
        {
            _diagnostics
                .RecordConnectionRejected();

            await WebsiteTrackingPipeMessageFraming
                .WriteAckAsync(
                    pipe,
                    WebsiteTrackingPipeAck.Reject(
                        "Pipe client identity rejected."
                    ),
                    cancellationToken
                );

            return;
        }

        _diagnostics
            .RecordConnectionAccepted();

        WebsiteTrackingObservation observation;

        try
        {
            observation =
                await WebsiteTrackingPipeMessageFraming
                    .ReadObservationAsync(
                        pipe,
                        cancellationToken
                    );
        }
        catch (
            Exception exception
        )
        {
            _logger.LogWarning(
                exception,
                "Website Tracking pipe observation could not be read."
            );

            await WebsiteTrackingPipeMessageFraming
                .WriteAckAsync(
                    pipe,
                    WebsiteTrackingPipeAck.Reject(
                        "Observation frame invalid."
                    ),
                    cancellationToken
                );

            return;
        }

        if (
            !_coordinator.TryAccept(
                observation,
                out WebsiteTrackingObservation accepted
            )
        )
        {
            await WebsiteTrackingPipeMessageFraming
                .WriteAckAsync(
                    pipe,
                    WebsiteTrackingPipeAck.Reject(
                        "Observation rejected by runtime validation."
                    ),
                    cancellationToken
                );

            return;
        }

        if (
            !_queue.TryWrite(
                accepted
            )
        )
        {
            await WebsiteTrackingPipeMessageFraming
                .WriteAckAsync(
                    pipe,
                    WebsiteTrackingPipeAck.Reject(
                        "Observation queue unavailable."
                    ),
                    cancellationToken
                );

            return;
        }

        _diagnostics
            .RecordObservationAccepted();

        await WebsiteTrackingPipeMessageFraming
            .WriteAckAsync(
                pipe,
                WebsiteTrackingPipeAck.Success(),
                cancellationToken
            );
    }
}