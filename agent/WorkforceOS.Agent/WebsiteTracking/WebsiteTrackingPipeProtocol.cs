using System.Text.Json;

namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingPipeProtocol
{
    private static readonly JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web)
            {
                PropertyNameCaseInsensitive =
                    true,
            };

    public static byte[] Serialize(
        WebsiteTrackingObservation observation
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        return JsonSerializer.SerializeToUtf8Bytes(
            observation,
            JsonOptions
        );
    }

    public static WebsiteTrackingObservation Deserialize(
        byte[] payload
    )
    {
        ArgumentNullException.ThrowIfNull(
            payload
        );

        if (
            payload.Length == 0
        )
        {
            throw new InvalidDataException(
                "Website Tracking pipe payload is empty."
            );
        }

        WebsiteTrackingObservation? observation =
            JsonSerializer.Deserialize<
                WebsiteTrackingObservation
            >(
                payload,
                JsonOptions
            );

        if (
            observation is null
        )
        {
            throw new InvalidDataException(
                "Website Tracking observation could not be deserialized."
            );
        }

        return observation;
    }

    public static byte[] SerializeAck(
        WebsiteTrackingPipeAck ack
    )
    {
        ArgumentNullException.ThrowIfNull(
            ack
        );

        return JsonSerializer.SerializeToUtf8Bytes(
            ack,
            JsonOptions
        );
    }

    public static WebsiteTrackingPipeAck DeserializeAck(
        byte[] payload
    )
    {
        ArgumentNullException.ThrowIfNull(
            payload
        );

        if (
            payload.Length == 0
        )
        {
            throw new InvalidDataException(
                "Website Tracking ACK payload is empty."
            );
        }

        WebsiteTrackingPipeAck? ack =
            JsonSerializer.Deserialize<
                WebsiteTrackingPipeAck
            >(
                payload,
                JsonOptions
            );

        if (
            ack is null
        )
        {
            throw new InvalidDataException(
                "Website Tracking ACK could not be deserialized."
            );
        }

        return ack;
    }
}