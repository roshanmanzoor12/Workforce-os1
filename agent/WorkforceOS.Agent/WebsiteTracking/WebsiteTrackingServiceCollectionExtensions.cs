using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingServiceCollectionExtensions
{
    public static IServiceCollection
        AddWorkforceWebsiteTracking(
            this IServiceCollection services,
            IConfiguration configuration
        )
    {
        ArgumentNullException.ThrowIfNull(
            services
        );

        ArgumentNullException.ThrowIfNull(
            configuration
        );

        services
            .AddOptions<
                WebsiteTrackingOptions
            >()
            .Bind(
                configuration.GetSection(
                    WebsiteTrackingOptions
                        .SectionName
                )
            )
            .Validate(
                options =>
                    options
                        .ObservationIntervalSeconds
                    is >= 1 and <= 300,
                "WebsiteTracking:ObservationIntervalSeconds must be between 1 and 300."
            )
            .Validate(
                options =>
                    options
                        .ReportIntervalSeconds
                    is >= 1 and <= 3600,
                "WebsiteTracking:ReportIntervalSeconds must be between 1 and 3600."
            )
            .Validate(
                options =>
                    options.ReportIntervalSeconds
                    >= options
                        .ObservationIntervalSeconds,
                "WebsiteTracking:ReportIntervalSeconds must be >= ObservationIntervalSeconds."
            )
            .Validate(
                options =>
                    options.MaximumDomainLength
                    is >= 1 and <= 255,
                "WebsiteTracking:MaximumDomainLength must be between 1 and 255."
            )
            .Validate(
                options =>
                    options.MaximumUrlLength
                    is >= 256 and <= 65536,
                "WebsiteTracking:MaximumUrlLength is invalid."
            )
            .Validate(
                options =>
                    options
                        .MaximumPageTitleLength
                    is >= 1 and <= 8192,
                "WebsiteTracking:MaximumPageTitleLength is invalid."
            )
            .Validate(
                options =>
                    options
                        .MonitoringDisclosureRequired,
                "WebsiteTracking:MonitoringDisclosureRequired must remain enabled."
            )
            .ValidateOnStart();

        // Browser bridge
        services.AddSingleton<
            BrowserBridgeValidator
        >();

        services.AddSingleton<
            BrowserNativeHostCommand
        >();

        // Runtime
        services.AddSingleton<
            WebsiteTrackingObservationValidator
        >();

        services.AddSingleton<
            WebsiteTrackingObservationDeduplicator
        >();

        services.AddSingleton<
            WebsiteTrackingRuntimeState
        >();

        services.AddSingleton<
            WebsiteTrackingRuntimeCoordinator
        >();

        services.AddSingleton<
            WebsiteTrackingHealthService
        >();

        // Persistent local IPC
        services.AddSingleton<
            WebsiteTrackingPipeDiagnostics
        >();

        services.AddSingleton<
            WebsiteTrackingObservationQueue
        >();

        services.AddSingleton<
            WebsiteTrackingPipeConnectionHandler
        >();

        services.AddSingleton<
            WebsiteTrackingPipeServer
        >();

        services.AddSingleton<
            WebsiteTrackingPipeClient
        >();

        // Credentials
        services.AddSingleton<
            DeviceCredentialStoreWebsiteTrackingAdapter
        >();

        services.AddSingleton<
            IWebsiteTrackingCredentialProvider
        >(
            serviceProvider =>
                serviceProvider
                    .GetRequiredService<
                        DeviceCredentialStoreWebsiteTrackingAdapter
                    >()
        );

        // Backend reporting
        services.AddSingleton<
            WebsiteTrackingApiClient
        >();

        services.AddSingleton<
            WebsiteTrackingReportingHealthState
        >();

        services.AddSingleton<
            WebsiteTrackingBackendReporter
        >();

        services.AddSingleton<
            WebsiteTrackingQueueDrainService
        >();

        services.AddHostedService<
            WebsiteTrackingBackendReportingWorker
        >();

        return services;
    }
}