namespace WorkforceOS.Agent.Runtime;

public sealed class HeartbeatRuntimeState
{
    private readonly object
        _syncRoot =
            new();

    private Guid _deviceUuid =
        Guid.Empty;

    private bool _hasSuccessfulHeartbeat;

    private DateTimeOffset?
        _lastSuccessfulHeartbeatAt;

    private int _consecutiveFailures;

    private int _currentHeartbeatIntervalSeconds =
        30;

    private string? _lastKnownDeviceStatus;

    public void Initialize(
        Guid deviceUuid
    )
    {
        lock (_syncRoot)
        {
            _deviceUuid =
                deviceUuid;

            _hasSuccessfulHeartbeat =
                false;

            _lastSuccessfulHeartbeatAt =
                null;

            _consecutiveFailures =
                0;

            _currentHeartbeatIntervalSeconds =
                30;

            _lastKnownDeviceStatus =
                null;
        }
    }

    public void RecordSuccess(
        Guid deviceUuid,
        DateTimeOffset heartbeatAt,
        int heartbeatIntervalSeconds,
        string deviceStatus
    )
    {
        lock (_syncRoot)
        {
            _deviceUuid =
                deviceUuid;

            _hasSuccessfulHeartbeat =
                true;

            _lastSuccessfulHeartbeatAt =
                heartbeatAt;

            _consecutiveFailures =
                0;

            _currentHeartbeatIntervalSeconds =
                heartbeatIntervalSeconds;

            _lastKnownDeviceStatus =
                deviceStatus;
        }
    }

    public void RecordFailure()
    {
        lock (_syncRoot)
        {
            _consecutiveFailures++;
        }
    }

    public HeartbeatHealthSnapshot GetSnapshot()
    {
        lock (_syncRoot)
        {
            return new HeartbeatHealthSnapshot
            {
                DeviceUuid =
                    _deviceUuid,

                HasSuccessfulHeartbeat =
                    _hasSuccessfulHeartbeat,

                LastSuccessfulHeartbeatAt =
                    _lastSuccessfulHeartbeatAt,

                ConsecutiveFailures =
                    _consecutiveFailures,

                CurrentHeartbeatIntervalSeconds =
                    _currentHeartbeatIntervalSeconds,

                LastKnownDeviceStatus =
                    _lastKnownDeviceStatus
            };
        }
    }
}