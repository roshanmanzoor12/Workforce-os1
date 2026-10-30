using System.Text.Json;

namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingCredentialProjection
{
    private static readonly JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web);

    public static bool TryProject(
        object credentials,
        out WebsiteTrackingDeviceCredentials projected
    )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        projected =
            null!;

        JsonElement element =
            JsonSerializer.SerializeToElement(
                credentials,
                credentials.GetType(),
                JsonOptions
            );

        if (
            !TryGetString(
                element,
                "deviceUuid",
                out string? deviceUuid
            )
        )
        {
            return false;
        }

        if (
            !TryGetString(
                element,
                "deviceSecret",
                out string? deviceSecret
            )
        )
        {
            return false;
        }

        if (
            !Guid.TryParse(
                deviceUuid,
                out Guid parsedDeviceUuid
            )
        )
        {
            return false;
        }

        if (
            string.IsNullOrWhiteSpace(
                deviceSecret
            )
        )
        {
            return false;
        }

        projected =
            new WebsiteTrackingDeviceCredentials
            {
                DeviceUuid =
                    parsedDeviceUuid.ToString(),

                DeviceSecret =
                    deviceSecret,
            };

        return true;
    }

    private static bool TryGetString(
        JsonElement element,
        string propertyName,
        out string? value
    )
    {
        value =
            null;

        if (
            !element.TryGetProperty(
                propertyName,
                out JsonElement property
            )
        )
        {
            return false;
        }

        if (
            property.ValueKind
            == JsonValueKind.String
        )
        {
            value =
                property.GetString();

            return (
                !string.IsNullOrWhiteSpace(
                    value
                )
            );
        }

        value =
            property.ToString();

        return (
            !string.IsNullOrWhiteSpace(
                value
            )
        );
    }
}