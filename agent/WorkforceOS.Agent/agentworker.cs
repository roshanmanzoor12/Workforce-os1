using System.Net;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Configuration;
using WorkforceOS.Agent.Enrollment;
using WorkforceOS.Agent.Runtime;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent;

public sealed class AgentWorker
    : BackgroundService
{
    private readonly ILogger<AgentWorker>
        _logger;

    private readonly EnrollmentService
        _enrollmentService;

    private readonly HeartbeatRunner
        _heartbeatRunner;

    private readonly AgentOptions
        _options;

    public AgentWorker(
        ILogger<AgentWorker> logger,
        EnrollmentService enrollmentService,
        HeartbeatRunner heartbeatRunner,
        IOptions<AgentOptions> options
    )
    {
        _logger =
            logger;

        _enrollmentService =
            enrollmentService;

        _heartbeatRunner =
            heartbeatRunner;

        _options =
            options.Value;
    }

    protected override async Task ExecuteAsync(
        CancellationToken stoppingToken
    )
    {
        _logger.LogInformation(
            "WorkforceOS Agent started."
        );

        int consecutiveFailures =
            0;

        while (
            !stoppingToken.IsCancellationRequested
        )
        {
            try
            {
                DeviceCredentials? credentials =
                    await _enrollmentService
                        .GetCredentialsAsync(
                            stoppingToken
                        );

                if (
                    credentials is null
                    || !credentials.IsValid()
                )
                {
                    consecutiveFailures =
                        0;

                    _logger.LogInformation(
                        "WorkforceOS Agent is not enrolled. Waiting for device enrollment."
                    );

                    await DelayAsync(
                        TimeSpan.FromSeconds(
                            _options
                                .InitialRetryDelaySeconds
                        ),
                        stoppingToken
                    );

                    continue;
                }

                consecutiveFailures =
                    0;

                _logger.LogInformation(
                    "Starting WorkforceOS heartbeat runtime for device {DeviceUuid}.",
                    credentials.DeviceUuid
                );

                await _heartbeatRunner.RunAsync(
                    credentials,
                    stoppingToken
                );
            }
            catch (
                WorkforceApiException exception
            )
            when (
                exception.StatusCode
                is HttpStatusCode.Unauthorized
                or HttpStatusCode.Forbidden
            )
            {
                consecutiveFailures++;

                TimeSpan delay =
                    GetRetryDelay(
                        consecutiveFailures
                    );

                _logger.LogWarning(
                    "WorkforceOS heartbeat authentication was rejected with HTTP status {StatusCode}. Retrying in {DelaySeconds} seconds.",
                    (int?)exception.StatusCode,
                    delay.TotalSeconds
                );

                await DelayAsync(
                    delay,
                    stoppingToken
                );
            }
            catch (
                WorkforceApiException exception
            )
            {
                consecutiveFailures++;

                TimeSpan delay =
                    GetRetryDelay(
                        consecutiveFailures
                    );

                _logger.LogWarning(
                    "WorkforceOS heartbeat request failed: {Message} Retrying in {DelaySeconds} seconds.",
                    exception.Message,
                    delay.TotalSeconds
                );

                await DelayAsync(
                    delay,
                    stoppingToken
                );
            }
            catch (
                HttpRequestException exception
            )
            {
                consecutiveFailures++;

                TimeSpan delay =
                    GetRetryDelay(
                        consecutiveFailures
                    );

                _logger.LogWarning(
                    "WorkforceOS backend is unreachable: {Message} Retrying in {DelaySeconds} seconds.",
                    exception.Message,
                    delay.TotalSeconds
                );

                await DelayAsync(
                    delay,
                    stoppingToken
                );
            }
            catch (
                OperationCanceledException
            )
            when (
                stoppingToken.IsCancellationRequested
            )
            {
                break;
            }
            catch (
                OperationCanceledException exception
            )
            {
                consecutiveFailures++;

                TimeSpan delay =
                    GetRetryDelay(
                        consecutiveFailures
                    );

                _logger.LogWarning(
                    "WorkforceOS heartbeat request timed out: {Message} Retrying in {DelaySeconds} seconds.",
                    exception.Message,
                    delay.TotalSeconds
                );

                await DelayAsync(
                    delay,
                    stoppingToken
                );
            }
            catch (
                Exception exception
            )
            {
                consecutiveFailures++;

                TimeSpan delay =
                    GetRetryDelay(
                        consecutiveFailures
                    );

                _logger.LogError(
                    exception,
                    "Unexpected WorkforceOS heartbeat runtime failure. Retrying in {DelaySeconds} seconds.",
                    delay.TotalSeconds
                );

                await DelayAsync(
                    delay,
                    stoppingToken
                );
            }
        }

        _logger.LogInformation(
            "WorkforceOS Agent stopped."
        );
    }

    private TimeSpan GetRetryDelay(
        int consecutiveFailures
    )
    {
        return RetryDelayCalculator.Calculate(
            consecutiveFailures,
            _options.InitialRetryDelaySeconds,
            _options.MaximumRetryDelaySeconds
        );
    }

    private static async Task DelayAsync(
        TimeSpan delay,
        CancellationToken cancellationToken
    )
    {
        try
        {
            await Task.Delay(
                delay,
                cancellationToken
            );
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken.IsCancellationRequested
        )
        {
            // Normal service shutdown.
        }
    }
}