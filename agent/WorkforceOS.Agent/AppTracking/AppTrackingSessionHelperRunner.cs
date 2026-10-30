using System.Diagnostics;
using System.Security.Principal;

namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingSessionHelperRunner
{
    private static readonly TimeSpan PipeTimeout =
        TimeSpan.FromSeconds(5);

    private readonly ForegroundAppDetector _detector;

    private readonly AppTrackingPipeClient _pipeClient;

    private readonly AppTrackingOptions _options;

    private readonly ILogger<AppTrackingSessionHelperRunner> _logger;

    public AppTrackingSessionHelperRunner(
        ForegroundAppDetector detector,
        AppTrackingPipeClient pipeClient,
        AppTrackingOptions options,
        ILogger<AppTrackingSessionHelperRunner> logger)
    {
        _detector = detector;
        _pipeClient = pipeClient;
        _options = options;
        _logger = logger;
    }

    public async Task RunAsync(
        CancellationToken cancellationToken)
    {
        _options.Validate();

        if (!_options.Enabled)
        {
            _logger.LogInformation(
                "WorkforceOS App Tracking helper is disabled.");

            return;
        }

        int sessionId =
            Process.GetCurrentProcess().SessionId;

        if (sessionId <= 0)
        {
            throw new InvalidOperationException(
                "App Tracking helper must run inside an interactive Windows user session.");
        }

        using WindowsIdentity identity =
            WindowsIdentity.GetCurrent(
                TokenAccessLevels.Query);

        string? userSid =
            identity.User?.Value;

        if (string.IsNullOrWhiteSpace(
            userSid))
        {
            throw new InvalidOperationException(
                "Unable to resolve interactive Windows user SID.");
        }

        _logger.LogInformation(
            "WorkforceOS disclosed App Tracking helper started. Session={SessionId}.",
            sessionId);

        TimeSpan interval =
            TimeSpan.FromSeconds(
                _options.ObservationIntervalSeconds);

        while (!cancellationToken.IsCancellationRequested)
        {
            try
            {
                ForegroundAppSnapshot? snapshot =
                    _detector.GetForegroundApplication(
                        _options.CaptureWindowTitles);

                if (snapshot is not null)
                {
                    AppTrackingObservation observation =
                        AppTrackingObservation.FromSnapshot(
                            snapshot,
                            _options);

                    AppTrackingSessionObservation payload =
                        new()
                        {
                            SessionId = sessionId,
                            UserSid = userSid,
                            ProcessName =
                                observation.ProcessName,
                            ExecutablePath =
                                observation.ExecutablePath,
                            WindowTitle =
                                observation.WindowTitle,
                            ObservedAt =
                                observation.ObservedAt,
                        };

                    await _pipeClient.SendAsync(
                        payload,
                        PipeTimeout,
                        cancellationToken);
                }
            }
            catch (OperationCanceledException)
                when (cancellationToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception)
            {
                _logger.LogError(
                    exception,
                    "WorkforceOS App Tracking helper observation failed.");
            }

            try
            {
                await Task.Delay(
                    interval,
                    cancellationToken);
            }
            catch (OperationCanceledException)
                when (cancellationToken.IsCancellationRequested)
            {
                break;
            }
        }

        _logger.LogInformation(
            "WorkforceOS App Tracking helper stopped.");
    }
}