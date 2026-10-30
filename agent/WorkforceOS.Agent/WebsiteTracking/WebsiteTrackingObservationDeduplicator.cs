namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class
    WebsiteTrackingObservationDeduplicator
{
    private readonly object _sync =
        new();

    private WebsiteTrackingObservation?
        _lastAcceptedObservation;

    public bool ShouldAccept(
        WebsiteTrackingObservation observation
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        lock (_sync)
        {
            if (
                _lastAcceptedObservation
                is null
            )
            {
                _lastAcceptedObservation =
                    observation;

                return true;
            }

            WebsiteTrackingObservation
                previous =
                    _lastAcceptedObservation;

            if (
                observation.ObservedAt
                <= previous.ObservedAt
            )
            {
                return false;
            }

            bool sameBrowser =
                string.Equals(
                    observation
                        .BrowserProcessName,
                    previous
                        .BrowserProcessName,
                    StringComparison
                        .OrdinalIgnoreCase
                );

            bool sameDomain =
                string.Equals(
                    observation.Domain,
                    previous.Domain,
                    StringComparison
                        .OrdinalIgnoreCase
                );

            bool sameUrl =
                string.Equals(
                    observation.PageUrl,
                    previous.PageUrl,
                    StringComparison.Ordinal
                );

            bool sameTitle =
                string.Equals(
                    observation.PageTitle,
                    previous.PageTitle,
                    StringComparison.Ordinal
                );

            bool duplicatePayload =
                sameBrowser
                && sameDomain
                && sameUrl
                && sameTitle
                && (
                    observation.ObservedAt
                    - previous.ObservedAt
                )
                < TimeSpan.FromSeconds(
                    1
                );

            if (
                duplicatePayload
            )
            {
                return false;
            }

            _lastAcceptedObservation =
                observation;

            return true;
        }
    }

    public void Reset()
    {
        lock (_sync)
        {
            _lastAcceptedObservation =
                null;
        }
    }
}