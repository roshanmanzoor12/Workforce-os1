namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingObservationDeduplicator
{
    private readonly object _sync =
        new();

    private AppTrackingSessionObservation? _lastAccepted;

    public bool ShouldAccept(
        AppTrackingSessionObservation observation)
    {
        ArgumentNullException.ThrowIfNull(
            observation);

        observation.Validate();

        lock (_sync)
        {
            if (_lastAccepted is null)
            {
                _lastAccepted =
                    observation;

                return true;
            }

            if (
                observation.ObservedAt
                <= _lastAccepted.ObservedAt)
            {
                return false;
            }

            bool sameApplication =
                string.Equals(
                    observation.ProcessName,
                    _lastAccepted.ProcessName,
                    StringComparison.OrdinalIgnoreCase)
                &&
                string.Equals(
                    observation.ExecutablePath
                        ?? string.Empty,
                    _lastAccepted.ExecutablePath
                        ?? string.Empty,
                    StringComparison.OrdinalIgnoreCase);

            bool sameTimestamp =
                observation.ObservedAt
                == _lastAccepted.ObservedAt;

            if (
                sameApplication
                && sameTimestamp)
            {
                return false;
            }

            _lastAccepted =
                observation;

            return true;
        }
    }

    public void Reset()
    {
        lock (_sync)
        {
            _lastAccepted =
                null;
        }
    }
}