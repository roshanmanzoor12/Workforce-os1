namespace WorkforceOS.Agent.Activity;

public sealed class ActivityRuntimeState
{
    private readonly object
        _sync =
            new();

    private ActivitySessionObservation?
        _latestObservation;

    private DateTimeOffset?
        _lastReceivedAt;

    private DateTimeOffset?
        _lastReportAt;

    private string?
        _lastError;

    public void RecordObservation(
        ActivitySessionObservation observation
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        lock (_sync)
        {
            _latestObservation =
                observation;

            _lastReceivedAt =
                DateTimeOffset.UtcNow;

            _lastError =
                null;
        }
    }

    public void RecordReported(
        DateTimeOffset reportedAt
    )
    {
        lock (_sync)
        {
            _lastReportAt =
                reportedAt;

            _lastError =
                null;
        }
    }

    public void RecordError(
        Exception exception
    )
    {
        ArgumentNullException.ThrowIfNull(
            exception
        );

        lock (_sync)
        {
            _lastError =
                exception.Message;
        }
    }

    public ActivityReceiverHealthSnapshot
        GetSnapshot()
    {
        lock (_sync)
        {
            return new ActivityReceiverHealthSnapshot
            {
                HasObservation =
                    _latestObservation
                    is not null,

                SessionId =
                    _latestObservation
                        ?.SessionId,

                UserSid =
                    _latestObservation
                        ?.UserSid,

                State =
                    _latestObservation
                        ?.State,

                IdleSeconds =
                    _latestObservation
                        ?.IdleSeconds,

                ObservedAt =
                    _latestObservation
                        ?.ObservedAt,

                LastReceivedAt =
                    _lastReceivedAt,

                LastReportAt =
                    _lastReportAt,

                LastError =
                    _lastError
            };
        }
    }

    public ActivitySessionObservation?
        GetLatestObservation()
    {
        lock (_sync)
        {
            return _latestObservation;
        }
    }
}