using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingObservationDeduplicatorTests
{
    [Fact]
    public void FirstObservationAccepted()
    {
        WebsiteTrackingObservationDeduplicator
            deduplicator =
                new();

        Assert.True(
            deduplicator.ShouldAccept(
                CreateObservation(
                    "github.com",
                    DateTimeOffset.UtcNow
                )
            )
        );
    }

    [Fact]
    public void OlderObservationRejected()
    {
        WebsiteTrackingObservationDeduplicator
            deduplicator =
                new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        Assert.True(
            deduplicator.ShouldAccept(
                CreateObservation(
                    "github.com",
                    now
                )
            )
        );

        Assert.False(
            deduplicator.ShouldAccept(
                CreateObservation(
                    "github.com",
                    now.AddSeconds(
                        -5
                    )
                )
            )
        );
    }

    [Fact]
    public void DomainSwitchAccepted()
    {
        WebsiteTrackingObservationDeduplicator
            deduplicator =
                new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        Assert.True(
            deduplicator.ShouldAccept(
                CreateObservation(
                    "github.com",
                    now
                )
            )
        );

        Assert.True(
            deduplicator.ShouldAccept(
                CreateObservation(
                    "youtube.com",
                    now.AddSeconds(
                        2
                    )
                )
            )
        );
    }

    private static
        WebsiteTrackingObservation
        CreateObservation(
            string domain,
            DateTimeOffset observedAt
        )
    {
        return new WebsiteTrackingObservation
        {
            BrowserName =
                "Google Chrome",

            BrowserProcessName =
                "chrome.exe",

            Domain =
                domain,

            ObservedAt =
                observedAt,
        };
    }
}