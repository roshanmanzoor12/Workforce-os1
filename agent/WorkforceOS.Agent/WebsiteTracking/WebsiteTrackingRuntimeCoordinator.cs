using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingRuntimeCoordinator
{
    private readonly
        WebsiteTrackingObservationValidator
        _validator;

    private readonly
        WebsiteTrackingObservationDeduplicator
        _deduplicator;

    private readonly
        WebsiteTrackingRuntimeState
        _runtimeState;

    private readonly
        ILogger<
            WebsiteTrackingRuntimeCoordinator
        >
        _logger;

    public WebsiteTrackingRuntimeCoordinator(
        WebsiteTrackingObservationValidator
            validator,
        WebsiteTrackingObservationDeduplicator
            deduplicator,
        WebsiteTrackingRuntimeState
            runtimeState,
        ILogger<
            WebsiteTrackingRuntimeCoordinator
        > logger
    )
    {
        _validator =
            validator;

        _deduplicator =
            deduplicator;

        _runtimeState =
            runtimeState;

        _logger =
            logger;
    }

    public bool TryAccept(
        WebsiteTrackingObservation observation,
        out WebsiteTrackingObservation
            acceptedObservation
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        acceptedObservation =
            observation;

        if (
            !_validator
                .TryValidateAndNormalize(
                    observation,
                    out WebsiteTrackingObservation
                        normalized,
                    out string?
                        validationError
                )
        )
        {
            _runtimeState.Reject();

            _logger.LogDebug(
                "Website Tracking observation rejected: {Reason}",
                validationError
            );

            return false;
        }

        if (
            !_deduplicator
                .ShouldAccept(
                    normalized
                )
        )
        {
            _runtimeState.Reject();

            _logger.LogDebug(
                "Website Tracking duplicate/old observation ignored."
            );

            return false;
        }

        _runtimeState.Accept(
            normalized
        );

        acceptedObservation =
            normalized;

        return true;
    }
}