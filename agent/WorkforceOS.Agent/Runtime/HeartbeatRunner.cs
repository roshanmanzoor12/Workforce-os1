using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Configuration;
using WorkforceOS.Agent.Enrollment;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Runtime;

public sealed class HeartbeatRunner
{
    private const int MinimumHeartbeatSeconds =
        5;

    private const int MaximumHeartbeatSeconds =
        300;

    private const int DefaultHeartbeatSeconds =
        30;

    private readonly WorkforceApiClient
        _apiClient;

    private readonly MachineIdentityProvider
        _machineIdentityProvider;

    private readonly AgentOptions
        _options;

    private readonly HeartbeatRuntimeState
        _runtimeState;

    private readonly ILogger<HeartbeatRunner>
        _logger;

    public HeartbeatRunner(
        WorkforceApiClient apiClient,
        MachineIdentityProvider machineIdentityProvider,
        IOptions<AgentOptions> options,
        HeartbeatRuntimeState runtimeState,
        ILogger<HeartbeatRunner> logger
    )
    {
        _apiClient =
            apiClient;

        _machineIdentityProvider =
            machineIdentityProvider;

        _options =
            options.Value;

        _runtimeState =
            runtimeState;

        _logger =
            logger;
    }

    public async Task RunAsync(
        DeviceCredentials credentials,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        if (
            !credentials.IsValid()
        )
        {
            throw new InvalidOperationException(
                "Cannot start heartbeat with invalid device credentials."
            );
        }

        _runtimeState.Initialize(
            credentials.DeviceUuid
        );

        MachineIdentity identity =
            await _machineIdentityProvider
                .GetAsync(
                    cancellationToken
                );

        bool heartbeatEstablished =
            false;

        int nextHeartbeatSeconds =
            DefaultHeartbeatSeconds;

        while (
            !cancellationToken
                .IsCancellationRequested
        )
        {
            try
            {
                DeviceHeartbeatRequest heartbeatRequest =
                    new()
                    {
                        AgentVersion =
                            _options.AgentVersion,

                        Hostname =
                            identity.Hostname
                    };

                DeviceHeartbeatResponse heartbeatResponse =
                    await _apiClient
                        .SendHeartbeatAsync(
                            credentials,
                            heartbeatRequest,
                            cancellationToken
                        );

                ValidateHeartbeatResponse(
                    credentials,
                    heartbeatResponse
                );

                nextHeartbeatSeconds =
                    NormalizeHeartbeatInterval(
                        heartbeatResponse
                            .NextHeartbeatSeconds
                    );

                _runtimeState.RecordSuccess(
                    deviceUuid:
                        heartbeatResponse.DeviceUuid,

                    heartbeatAt:
                        heartbeatResponse.HeartbeatAt,

                    heartbeatIntervalSeconds:
                        nextHeartbeatSeconds,

                    deviceStatus:
                        heartbeatResponse.Status
                );

                if (
                    !heartbeatEstablished
                )
                {
                    heartbeatEstablished =
                        true;

                    _logger.LogInformation(
                        "WorkforceOS heartbeat established for device {DeviceUuid}. Server interval: {HeartbeatSeconds} seconds.",
                        heartbeatResponse.DeviceUuid,
                        nextHeartbeatSeconds
                    );
                }
                else
                {
                    _logger.LogDebug(
                        "WorkforceOS heartbeat acknowledged for device {DeviceUuid} at {HeartbeatAt}.",
                        heartbeatResponse.DeviceUuid,
                        heartbeatResponse.HeartbeatAt
                    );
                }

                await Task.Delay(
                    TimeSpan.FromSeconds(
                        nextHeartbeatSeconds
                    ),
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
            catch
            {
                _runtimeState.RecordFailure();

                throw;
            }
        }
    }

    private static void ValidateHeartbeatResponse(
        DeviceCredentials credentials,
        DeviceHeartbeatResponse response
    )
    {
        if (
            response.DeviceUuid
            != credentials.DeviceUuid
        )
        {
            throw new InvalidOperationException(
                "Heartbeat response device identity does not match local enrollment."
            );
        }

        if (
            string.IsNullOrWhiteSpace(
                response.Status
            )
        )
        {
            throw new InvalidOperationException(
                "Heartbeat response did not contain a valid device status."
            );
        }

        if (
            response.HeartbeatAt
            == default
        )
        {
            throw new InvalidOperationException(
                "Heartbeat response did not contain a valid server timestamp."
            );
        }
    }

    private static int NormalizeHeartbeatInterval(
        int requestedSeconds
    )
    {
        return Math.Clamp(
            requestedSeconds,
            MinimumHeartbeatSeconds,
            MaximumHeartbeatSeconds
        );
    }
}