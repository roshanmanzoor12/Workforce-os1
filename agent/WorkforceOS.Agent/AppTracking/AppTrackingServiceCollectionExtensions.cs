using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using WorkforceOS.Agent.Api;

namespace WorkforceOS.Agent.AppTracking;

public static class AppTrackingServiceCollectionExtensions
{
    public static IServiceCollection AddWorkforceAppTracking(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(
            services);

        ArgumentNullException.ThrowIfNull(
            configuration);

        AppTrackingOptions options =
            new();

        IConfigurationSection section =
            configuration.GetSection(
                AppTrackingOptions.SectionName);

        section.Bind(
            options);

        options.Validate();

        services.AddSingleton(
            options);

        services.AddSingleton<
            ForegroundAppDetector>();

        services.AddSingleton<
            AppTrackingPipeClient>();

        services.AddSingleton<
            AppTrackingRuntimeState>();

        services.AddSingleton<
            AppTrackingHealthService>();

        services.AddSingleton<
            AppTrackingObservationDeduplicator>();

        services.AddSingleton<
            AppTrackingRuntimeCoordinator>();

        services.AddSingleton<
            AppTrackingObservationValidator>();

        services.AddSingleton<
            AppTrackingPipeServer>();

        services.AddSingleton<
            AppTrackingApiClient>();

        services.AddSingleton<
            AppTrackingBackendReporter>();

        services.AddSingleton<
            AppTrackingSessionHelperRunner>();

        services.AddSingleton<
            AppTrackingSessionHelperCommand>();

        services.AddHostedService<
            AppTrackingServiceReceiver>();

        services.AddHostedService<
            AppTrackingBackendReportingWorker>();

        return services;
    }
}