using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingHealthFormatterTests
{
    [Fact]
    public void EmptySnapshotFormatsCleanly()
    {
        WebsiteTrackingHealthSnapshot
            snapshot =
                new(
                    HasObservation:
                        false,

                    BrowserProcessName:
                        null,

                    Domain:
                        null,

                    LastObservedAt:
                        null,

                    LastReceivedAt:
                        null,

                    AcceptedCount:
                        0,

                    RejectedCount:
                        0
                );

        string value =
            WebsiteTrackingHealthFormatter
                .Format(
                    snapshot
                );

        Assert.Contains(
            "no observation",
            value,
            StringComparison.OrdinalIgnoreCase
        );
    }

    [Fact]
    public void ActiveSnapshotContainsDomain()
    {
        WebsiteTrackingHealthSnapshot
            snapshot =
                new(
                    HasObservation:
                        true,

                    BrowserProcessName:
                        "chrome.exe",

                    Domain:
                        "github.com",

                    LastObservedAt:
                        DateTimeOffset.UtcNow,

                    LastReceivedAt:
                        DateTimeOffset.UtcNow,

                    AcceptedCount:
                        10,

                    RejectedCount:
                        2
                );

        string value =
            WebsiteTrackingHealthFormatter
                .Format(
                    snapshot
                );

        Assert.Contains(
            "github.com",
            value
        );

        Assert.Contains(
            "chrome.exe",
            value
        );
    }
}