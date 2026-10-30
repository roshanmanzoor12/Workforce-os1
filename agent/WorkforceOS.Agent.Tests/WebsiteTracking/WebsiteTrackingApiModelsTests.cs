using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingApiModelsTests
{
    [Fact]
    public void ObservationMapsToApiModel()
    {
        DateTimeOffset observedAt =
            DateTimeOffset.UtcNow;

        WebsiteTrackingObservation observation =
            new()
            {
                BrowserName =
                    "Google Chrome",

                BrowserProcessName =
                    "chrome.exe",

                Domain =
                    "github.com",

                PageUrl =
                    null,

                PageTitle =
                    null,

                ObservedAt =
                    observedAt,
            };

        WebsiteTrackingApiObservationRequest request =
            WebsiteTrackingApiObservationRequest
                .FromObservation(
                    observation
                );

        Assert.Equal(
            "Google Chrome",
            request.BrowserName
        );

        Assert.Equal(
            "chrome.exe",
            request.BrowserProcessName
        );

        Assert.Equal(
            "github.com",
            request.Domain
        );

        Assert.Null(
            request.PageUrl
        );

        Assert.Null(
            request.PageTitle
        );

        Assert.Equal(
            observedAt,
            request.ObservedAt
        );
    }
}