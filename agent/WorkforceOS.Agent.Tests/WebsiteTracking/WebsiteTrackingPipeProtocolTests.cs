using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingPipeProtocolTests
{
    [Fact]
    public void ObservationRoundTripWorks()
    {
        WebsiteTrackingObservation
            original =
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
                        DateTimeOffset.UtcNow,
                };

        byte[] payload =
            WebsiteTrackingPipeProtocol
                .Serialize(
                    original
                );

        WebsiteTrackingObservation
            restored =
                WebsiteTrackingPipeProtocol
                    .Deserialize(
                        payload
                    );

        Assert.Equal(
            original.BrowserName,
            restored.BrowserName
        );

        Assert.Equal(
            original.BrowserProcessName,
            restored.BrowserProcessName
        );

        Assert.Equal(
            original.Domain,
            restored.Domain
        );

        Assert.Null(
            restored.PageUrl
        );

        Assert.Null(
            restored.PageTitle
        );
    }

    [Fact]
    public void EmptyPayloadRejected()
    {
        Assert.Throws<
            InvalidDataException
        >(
            () =>
                WebsiteTrackingPipeProtocol
                    .Deserialize(
                        Array.Empty<byte>()
                    )
        );
    }
}