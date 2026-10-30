using System.Text;
using System.Text.Json;

namespace WorkforceOS.Agent.Activity;

public static class ActivityPipeProtocol
{
    public const int MaximumPayloadBytes =
        16 * 1024;

    private static readonly JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web)
            {
                PropertyNameCaseInsensitive =
                    false
            };

    public static byte[] Serialize(
        ActivitySessionObservation observation
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        observation.Validate();

        byte[] payload =
            JsonSerializer.SerializeToUtf8Bytes(
                observation,
                JsonOptions
            );

        if (
            payload.Length
            <= 0
            ||
            payload.Length
            > MaximumPayloadBytes
        )
        {
            throw new InvalidOperationException(
                "Activity IPC payload size is invalid."
            );
        }

        return payload;
    }

    public static ActivitySessionObservation Deserialize(
        ReadOnlySpan<byte> payload
    )
    {
        if (
            payload.Length
            <= 0
            ||
            payload.Length
            > MaximumPayloadBytes
        )
        {
            throw new InvalidOperationException(
                "Activity IPC payload size is invalid."
            );
        }

        ActivitySessionObservation? observation =
            JsonSerializer.Deserialize<
                ActivitySessionObservation
            >(
                payload,
                JsonOptions
            );

        if (
            observation is null
        )
        {
            throw new InvalidOperationException(
                "Activity IPC payload was empty or invalid."
            );
        }

        observation.Validate();

        return observation;
    }

    public static async Task WriteAsync(
        Stream stream,
        ActivitySessionObservation observation,
        CancellationToken cancellationToken = default
    )
    {
        ArgumentNullException.ThrowIfNull(
            stream
        );

        byte[] payload =
            Serialize(
                observation
            );

        byte[] lengthPrefix =
            BitConverter.GetBytes(
                payload.Length
            );

        await stream.WriteAsync(
            lengthPrefix,
            cancellationToken
        );

        await stream.WriteAsync(
            payload,
            cancellationToken
        );

        await stream.FlushAsync(
            cancellationToken
        );
    }

    public static async Task<ActivitySessionObservation>
        ReadAsync(
            Stream stream,
            CancellationToken cancellationToken = default
        )
    {
        ArgumentNullException.ThrowIfNull(
            stream
        );

        byte[] lengthPrefix =
            new byte[
                sizeof(int)
            ];

        await ReadExactlyAsync(
            stream,
            lengthPrefix,
            cancellationToken
        );

        int payloadLength =
            BitConverter.ToInt32(
                lengthPrefix,
                0
            );

        if (
            payloadLength
            <= 0
            ||
            payloadLength
            > MaximumPayloadBytes
        )
        {
            throw new InvalidOperationException(
                "Activity IPC payload length is invalid."
            );
        }

        byte[] payload =
            new byte[
                payloadLength
            ];

        await ReadExactlyAsync(
            stream,
            payload,
            cancellationToken
        );

        return Deserialize(
            payload
        );
    }

    private static async Task ReadExactlyAsync(
        Stream stream,
        byte[] buffer,
        CancellationToken cancellationToken
    )
    {
        int offset =
            0;

        while (
            offset
            < buffer.Length
        )
        {
            int bytesRead =
                await stream.ReadAsync(
                    buffer.AsMemory(
                        offset,
                        buffer.Length
                        - offset
                    ),
                    cancellationToken
                );

            if (
                bytesRead
                == 0
            )
            {
                throw new EndOfStreamException(
                    "Activity IPC connection closed before the complete payload was received."
                );
            }

            offset +=
                bytesRead;
        }
    }
}