using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingReportResultTests
{
    [Fact]
    public void SuccessReportsSuccess()
    {
        WebsiteTrackingReportResult result =
            new()
            {
                Status =
                    WebsiteTrackingReportStatus
                        .Success,
            };

        Assert.True(
            result.IsSuccess
        );
    }

    [Theory]
    [InlineData(
        WebsiteTrackingReportStatus
            .CredentialsUnavailable
    )]
    [InlineData(
        WebsiteTrackingReportStatus
            .BackendRejected
    )]
    [InlineData(
        WebsiteTrackingReportStatus
            .Failed
    )]
    public void FailureStatusesAreNotSuccessful(
        WebsiteTrackingReportStatus status
    )
    {
        WebsiteTrackingReportResult result =
            new()
            {
                Status =
                    status,
            };

        Assert.False(
            result.IsSuccess
        );
    }
}