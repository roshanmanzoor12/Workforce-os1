using WorkforceOS.Agent.LiveScreen;

namespace WorkforceOS.Agent.Tests.LiveScreen;

public sealed class LiveScreenInboxValidationTests
{
    [Fact]
    public void EmptyInboxIsValid()
    {
        Assert.True(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse()));
    }

    [Fact]
    public void NullInboxIsInvalid()
    {
        Assert.False(LiveScreenInboxClient.IsValid(null));
    }

    [Fact]
    public void MissingSessionIdentityIsInvalid()
    {
        Assert.False(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse
        {
            Sessions = new List<LiveScreenInboxItem> { new()
            {
                SessionId = Guid.Empty, Status = "requested",
                ExpiresAt = DateTimeOffset.UtcNow.AddMinutes(1)
            }}
        }));
    }

    [Fact]
    public void InvalidStatusIsRejected()
    {
        Assert.False(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse
        {
            Sessions = new List<LiveScreenInboxItem> { new()
            {
                SessionId = Guid.NewGuid(), Status = "active",
                ExpiresAt = DateTimeOffset.UtcNow.AddMinutes(1)
            }}
        }));
    }

    [Fact]
    public void RequestedSessionIsAcceptedForReadOnlyDiscovery()
    {
        Assert.True(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse
        {
            CaptureAuthorized = false,
            Sessions = new List<LiveScreenInboxItem> { new()
            {
                SessionId = Guid.NewGuid(), Status = "requested",
                ExpiresAt = DateTimeOffset.UtcNow.AddMinutes(1),
                ConsentRequired = true, VisibleIndicatorRequired = true
            }}
        }));
    }
}
