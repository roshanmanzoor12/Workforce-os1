using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingPipeAckTests
{
    [Fact]
    public void SuccessAckIsAccepted()
    {
        WebsiteTrackingPipeAck ack =
            WebsiteTrackingPipeAck
                .Success();

        Assert.True(
            ack.Accepted
        );

        Assert.Null(
            ack.Error
        );
    }

    [Fact]
    public void RejectAckContainsReason()
    {
        WebsiteTrackingPipeAck ack =
            WebsiteTrackingPipeAck
                .Reject(
                    "test"
                );

        Assert.False(
            ack.Accepted
        );

        Assert.Equal(
            "test",
            ack.Error
        );
    }

    [Fact]
    public void AckRoundTripWorks()
    {
        WebsiteTrackingPipeAck original =
            WebsiteTrackingPipeAck
                .Success();

        byte[] payload =
            WebsiteTrackingPipeProtocol
                .SerializeAck(
                    original
                );

        WebsiteTrackingPipeAck restored =
            WebsiteTrackingPipeProtocol
                .DeserializeAck(
                    payload
                );

        Assert.True(
            restored.Accepted
        );
    }
}