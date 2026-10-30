using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using WorkforceOS.Agent.Activity;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.AppTracking;
using WorkforceOS.Agent.Configuration;
using WorkforceOS.Agent.Enrollment;
using WorkforceOS.Agent.Runtime;
using WorkforceOS.Agent.Security;
using WorkforceOS.Agent.WebsiteTracking;

namespace WorkforceOS.Agent;

public static class Program
{
    public static async Task<int> Main(
        string[] args
    )
    {
        // CLI help must exit before hosted services register or named pipes bind.
        if (args.Any(argument =>
                string.Equals(argument, "--help", StringComparison.OrdinalIgnoreCase)
                || string.Equals(argument, "-h", StringComparison.OrdinalIgnoreCase)))
        {
            Console.WriteLine("WorkforceOS Agent: --enroll, --status, --presence, --reset-enrollment, --activity-session-helper");
            Console.WriteLine("No command starts the agent host. Do not launch a second service instance interactively.");
            return 0;
        }

        // =================================================
        // SPECIAL INTERACTIVE MODES
        // =================================================

        bool appTrackingHelperRequested =
            AppTrackingHelperBootstrap
                .IsRequested(
                    args
                );

        bool websiteNativeHostRequested =
            BrowserNativeHostBootstrap
                .IsRequested(
                    args
                );

        if (
            appTrackingHelperRequested
            && websiteNativeHostRequested
        )
        {
            Console.Error.WriteLine(
                "Only one Agent helper mode can run at a time."
            );

            return 1;
        }

        // =================================================
        // EXISTING COMMAND LINE
        // =================================================

        AgentCommandLineOptions?
            commandLineOptions =
                null;

        if (
            !appTrackingHelperRequested
            && !websiteNativeHostRequested
        )
        {
            try
            {
                commandLineOptions =
                    AgentCommandLineOptions
                        .Parse(
                            args
                        );
            }
            catch (
                ArgumentException exception
            )
            {
                Console.Error.WriteLine(
                    exception.Message
                );

                return 1;
            }
        }

        // =================================================
        // HOST ARGUMENTS
        // =================================================

        string[] hostArguments;

        if (
            appTrackingHelperRequested
        )
        {
            hostArguments =
                args
                    .Where(
                        argument =>
                            !string.Equals(
                                argument,
                                AppTrackingCommandLine
                                    .SessionHelperArgument,
                                StringComparison
                                    .OrdinalIgnoreCase
                            )
                    )
                    .ToArray();
        }
        else if (
            websiteNativeHostRequested
        )
        {
            hostArguments =
                WebsiteTrackingCommandLine
                    .RemoveNativeHostArgument(
                        args
                    );
        }
        else
        {
            hostArguments =
                AgentCommandLineOptions
                    .GetHostArguments(
                        args
                    );
        }

        HostApplicationBuilder builder =
            Host.CreateApplicationBuilder(
                hostArguments
            );

        // =================================================
        // WINDOWS SERVICE
        // =================================================

        builder.Services.AddWindowsService(
            options =>
            {
                options.ServiceName =
                    "WorkforceOS Agent";
            }
        );

        // =================================================
        // READ-ONLY DEVICE LIVE-SESSION DISCOVERY
        // Does not authorize or start screen capture.
        builder.Services.AddSingleton<WorkforceOS.Agent.LiveScreen.LiveScreenInboxClient>();
        builder.Services.AddHostedService<WorkforceOS.Agent.LiveScreen.LiveScreenInboxWorker>();

        // AGENT CONFIGURATION
        // =================================================

        builder.Services
            .AddOptions<AgentOptions>()
            .Bind(
                builder.Configuration
                    .GetSection(
                        AgentOptions.SectionName
                    )
            )
            .Validate(
                options =>
                    Uri.TryCreate(
                        options.ApiBaseUrl,
                        UriKind.Absolute,
                        out Uri? uri
                    )
                    && (
                        uri.Scheme
                        == Uri.UriSchemeHttp
                        || uri.Scheme
                        == Uri.UriSchemeHttps
                    ),
                "Agent:ApiBaseUrl must be a valid HTTP or HTTPS URL."
            )
            .Validate(
                options =>
                    !string.IsNullOrWhiteSpace(
                        options.RegistrationPath
                    )
                    && options.RegistrationPath
                        .StartsWith(
                            "/",
                            StringComparison.Ordinal
                        ),
                "Agent:RegistrationPath must be an absolute API path."
            )
            .Validate(
                options =>
                    !string.IsNullOrWhiteSpace(
                        options.DeviceIdentityPath
                    )
                    && options.DeviceIdentityPath
                        .StartsWith(
                            "/",
                            StringComparison.Ordinal
                        ),
                "Agent:DeviceIdentityPath must be an absolute API path."
            )
            .Validate(
                options =>
                    options.HttpTimeoutSeconds
                    is >= 5 and <= 300,
                "Agent:HttpTimeoutSeconds must be between 5 and 300."
            )
            .Validate(
                options =>
                    options.InitialRetryDelaySeconds
                    is >= 1 and <= 300,
                "Agent:InitialRetryDelaySeconds must be between 1 and 300."
            )
            .Validate(
                options =>
                    options.MaximumRetryDelaySeconds
                    is >= 5 and <= 3600,
                "Agent:MaximumRetryDelaySeconds must be between 5 and 3600."
            )
            .Validate(
                options =>
                    options.MaximumRetryDelaySeconds
                    >= options.InitialRetryDelaySeconds,
                "Agent:MaximumRetryDelaySeconds must be greater than or equal to InitialRetryDelaySeconds."
            )
            .Validate(
                options =>
                    !string.IsNullOrWhiteSpace(
                        options.AgentName
                    ),
                "Agent:AgentName is required."
            )
            .Validate(
                options =>
                    !string.IsNullOrWhiteSpace(
                        options.AgentVersion
                    ),
                "Agent:AgentVersion is required."
            )
            .ValidateOnStart();

        // =================================================
        // ACTIVITY CONFIGURATION
        // =================================================

        builder.Services
            .AddOptions<ActivityOptions>()
            .Bind(
                builder.Configuration
                    .GetSection(
                        ActivityOptions.SectionName
                    )
            )
            .Validate(
                options =>
                    options.IdleThresholdSeconds
                    is >= 5 and <= 86_400,
                "Activity:IdleThresholdSeconds must be between 5 and 86400."
            )
            .Validate(
                options =>
                    options.ObservationIntervalSeconds
                    is >= 1 and <= 300,
                "Activity:ObservationIntervalSeconds must be between 1 and 300."
            )
            .Validate(
                options =>
                    options.ReportIntervalSeconds
                    is >= 1 and <= 3600,
                "Activity:ReportIntervalSeconds must be between 1 and 3600."
            )
            .Validate(
                options =>
                    options.ReportIntervalSeconds
                    >= options.ObservationIntervalSeconds,
                "Activity:ReportIntervalSeconds must be greater than or equal to ObservationIntervalSeconds."
            )
            .ValidateOnStart();

        // =================================================
        // LOGGING
        // =================================================

        builder.Logging.ClearProviders();

        /*
         * Native Messaging reserves stdout for its binary framed
         * protocol. Never write normal application logs to stdout
         * while running native-host mode.
         */
        if (
            !websiteNativeHostRequested
        )
        {
            builder.Logging.AddSimpleConsole(
                options =>
                {
                    options.SingleLine =
                        true;

                    options.TimestampFormat =
                        "yyyy-MM-dd HH:mm:ss ";
                }
            );
        }

        // =================================================
        // HTTP
        // =================================================

        builder.Services.AddHttpClient(
            WorkforceApiClient.HttpClientName,
            (
                serviceProvider,
                client
            ) =>
            {
                AgentOptions options =
                    serviceProvider
                        .GetRequiredService<
                            IOptions<AgentOptions>
                        >()
                        .Value;

                client.BaseAddress =
                    new Uri(
                        options.ApiBaseUrl,
                        UriKind.Absolute
                    );

                client.Timeout =
                    TimeSpan.FromSeconds(
                        options.HttpTimeoutSeconds
                    );

                client.DefaultRequestHeaders
                    .Accept
                    .Clear();

                client.DefaultRequestHeaders
                    .Accept
                    .ParseAdd(
                        "application/json"
                    );

                client.DefaultRequestHeaders
                    .UserAgent
                    .ParseAdd(
                        $"WorkforceOS-Agent/{options.AgentVersion}"
                    );
            }
        );

        // =================================================
        // MACHINE IDENTITY
        // =================================================

        builder.Services.AddSingleton<
            MachineIdentityProvider
        >();

        // =================================================
        // SECURITY
        // =================================================

        builder.Services.AddSingleton<
            DeviceCredentialStore
        >();

        // =================================================
        // API
        // =================================================

        builder.Services.AddSingleton<
            WorkforceApiClient
        >();

        builder.Services.AddSingleton<
            DevicePresenceClient
        >();

        builder.Services.AddSingleton<
            ActivityApiClient
        >();

        // =================================================
        // ENROLLMENT
        // =================================================

        builder.Services.AddSingleton<
            EnrollmentService
        >();

        builder.Services.AddSingleton<
            AgentBootstrapper
        >();

        // =================================================
        // HEARTBEAT
        // =================================================

        builder.Services.AddSingleton<
            HeartbeatRuntimeState
        >();

        builder.Services.AddSingleton<
            HeartbeatRunner
        >();

        // =================================================
        // PHASE 08 ACTIVITY
        // =================================================

        builder.Services.AddSingleton<
            LastInputDetector
        >();

        builder.Services.AddSingleton<
            ActivityPipeClient
        >();

        builder.Services.AddSingleton<
            ActivityObservationValidator
        >();

        builder.Services.AddSingleton<
            ActivityPipeServer
        >();

        builder.Services.AddSingleton<
            ActivityRuntimeState
        >();

        builder.Services.AddSingleton<
            ActivityReporter
        >();

        builder.Services.AddSingleton<
            ActivityBackendReporter
        >();

        builder.Services.AddSingleton<
            ActivitySessionHelperRunner
        >();

        builder.Services.AddSingleton<
            ActivitySessionHelperCommand
        >();

        // =================================================
        // PHASE 10 APP TRACKING
        // =================================================

        builder.Services.AddWorkforceAppTracking(
            builder.Configuration
        );

        // =================================================
        // PHASE 11 WEBSITE TRACKING
        // =================================================

        builder.Services
            .AddWorkforceWebsiteTracking(
                builder.Configuration
            );

        // =================================================
        // NORMAL AGENT BACKGROUND SERVICES
        // =================================================

        if (
            !appTrackingHelperRequested
            && !websiteNativeHostRequested
            && commandLineOptions is not null
            && commandLineOptions.Mode
                == AgentCommandMode.RunAgent
        )
        {
            builder.Services.AddHostedService<
                AgentWorker
            >();

            builder.Services.AddHostedService<
                ActivityServiceReceiver
            >();

            builder.Services.AddHostedService<
                ActivityBackendReportingWorker
            >();

            builder.Services.AddHostedService<
                WebsiteTrackingServiceReceiver
            >();
        }

        // =================================================
        // BUILD HOST
        // =================================================

        using IHost host =
            builder.Build();

        // =================================================
        // PHASE 11 BROWSER NATIVE HOST MODE
        // =================================================

        if (
            websiteNativeHostRequested
        )
        {
            using CancellationTokenSource
                cancellationSource =
                    new();

            Console.CancelKeyPress +=
                (
                    sender,
                    eventArgs
                ) =>
                {
                    eventArgs.Cancel =
                        true;

                    cancellationSource.Cancel();
                };

            return await BrowserNativeHostBootstrap
                .RunAsync(
                    host.Services,
                    cancellationSource.Token
                );
        }

        // =================================================
        // PHASE 10 APP TRACKING HELPER
        // =================================================

        if (
            appTrackingHelperRequested
        )
        {
            using CancellationTokenSource
                cancellationSource =
                    new();

            Console.CancelKeyPress +=
                (
                    sender,
                    eventArgs
                ) =>
                {
                    eventArgs.Cancel =
                        true;

                    cancellationSource.Cancel();
                };

            return await AppTrackingHelperBootstrap
                .RunAsync(
                    host.Services,
                    cancellationSource.Token
                );
        }

        if (
            commandLineOptions is null
        )
        {
            throw new InvalidOperationException(
                "Agent command-line mode was not resolved."
            );
        }

        // =================================================
        // PHASE 08 ACTIVITY HELPER
        // =================================================

        if (
            commandLineOptions.Mode
            == AgentCommandMode
                .ActivitySessionHelper
        )
        {
            ActivitySessionHelperCommand
                command =
                    host.Services
                        .GetRequiredService<
                            ActivitySessionHelperCommand
                        >();

            using CancellationTokenSource
                cancellationSource =
                    new();

            Console.CancelKeyPress +=
                (
                    sender,
                    eventArgs
                ) =>
                {
                    eventArgs.Cancel =
                        true;

                    cancellationSource.Cancel();
                };

            return await command.RunAsync(
                cancellationSource.Token
            );
        }

        // =================================================
        // EXISTING INTERACTIVE MODES
        // =================================================

        if (
            commandLineOptions.Mode
            != AgentCommandMode.RunAgent
        )
        {
            AgentBootstrapper bootstrapper =
                host.Services
                    .GetRequiredService<
                        AgentBootstrapper
                    >();

            return await bootstrapper.ExecuteAsync(
                commandLineOptions
            );
        }

        // =================================================
        // WINDOWS SERVICE
        // =================================================

        await host.RunAsync();

        return 0;
    }
}