using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class
    WebsiteTrackingCredentialProjectionTests
{
    private sealed record FakeCredentials
    {
        public required Guid DeviceUuid
        {
            get;
            init;
        }

        public required string DeviceSecret
        {
            get;
            init;
        }
    }

    [Fact]
    public void ValidCredentialsProject()
    {
        Guid deviceUuid =
            Guid.NewGuid();

        FakeCredentials source =
            new()
            {
                DeviceUuid =
                    deviceUuid,

                DeviceSecret =
                    "wfds_test_secret_1234567890",
            };

        bool result =
            WebsiteTrackingCredentialProjection
                .TryProject(
                    source,
                    out WebsiteTrackingDeviceCredentials
                        projected
                );

        Assert.True(
            result
        );

        Assert.Equal(
            deviceUuid.ToString(),
            projected.DeviceUuid
        );

        Assert.Equal(
            "wfds_test_secret_1234567890",
            projected.DeviceSecret
        );

        Assert.True(
            projected.IsValid()
        );
    }

    [Fact]
    public void MissingSecretRejected()
    {
        var source =
            new
            {
                DeviceUuid =
                    Guid.NewGuid(),
            };

        Assert.False(
            WebsiteTrackingCredentialProjection
                .TryProject(
                    source,
                    out _
                )
        );
    }

    [Fact]
    public void InvalidUuidRejected()
    {
        var source =
            new
            {
                DeviceUuid =
                    "not-a-uuid",

                DeviceSecret =
                    "wfds_test_secret_1234567890",
            };

        Assert.False(
            WebsiteTrackingCredentialProjection
                .TryProject(
                    source,
                    out _
                )
        );
    }
}