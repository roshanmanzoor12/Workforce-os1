using System.Buffers.Binary;

namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingPipeMessageFraming
{
    private const int PrefixLength =
        sizeof(int);

    public static async Task WriteObservationAsync(
        Stream stream,
        WebsiteTrackingObservation observation,
        CancellationToken cancellationToken
    )
    {
        byte[] payload =
            WebsiteTrackingPipeProtocol
                .Serialize(
                    observation
                );

        await WritePayloadAsync(
            stream,
            payload,
            cancellationToken
        );
    }

    public static async Task<
        WebsiteTrackingObservation
    > ReadObservationAsync(
        Stream stream,
        CancellationToken cancellationToken
    )
    {
        byte[] payload =
            await ReadPayloadAsync(
                stream,
                cancellationToken
            );

        return WebsiteTrackingPipeProtocol
            .Deserialize(
                payload
            );
    }

    public static async Task WriteAckAsync(
        Stream stream,
        WebsiteTrackingPipeAck ack,
        CancellationToken cancellationToken
    )
    {
        byte[] payload =
            WebsiteTrackingPipeProtocol
                .SerializeAck(
                    ack
                );

        await WritePayloadAsync(
            stream,
            payload,
            cancellationToken
        );
    }

    public static async Task<
        WebsiteTrackingPipeAck
    > ReadAckAsync(
        Stream stream,
        CancellationToken cancellationToken
    )
    {
        byte[] payload =
            await ReadPayloadAsync(
                stream,
                cancellationToken
            );

        return WebsiteTrackingPipeProtocol
            .DeserializeAck(
                payload
            );
    }

    private static async Task WritePayloadAsync(
        Stream stream,
        byte[] payload,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            stream
        );

        if (
            payload.Length <= 0
            || payload.Length
            > WebsiteTrackingPipeNames
                .MaximumMessageBytes
        )
        {
            throw new InvalidDataException(
                "Website Tracking framed payload size is invalid."
            );
        }

        byte[] prefix =
            new byte[
                PrefixLength
            ];

        BinaryPrimitives
            .WriteInt32LittleEndian(
                prefix,
                payload.Length
            );

        await stream.WriteAsync(
            prefix,
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

    private static async Task<byte[]>
        ReadPayloadAsync(
            Stream stream,
            CancellationToken cancellationToken
        )
    {
        ArgumentNullException.ThrowIfNull(
            stream
        );

        byte[] prefix =
            new byte[
                PrefixLength
            ];

        await ReadExactlyAsync(
            stream,
            prefix,
            cancellationToken
        );

        int payloadLength =
            BinaryPrimitives
                .ReadInt32LittleEndian(
                    prefix
                );

        if (
            payloadLength <= 0
            || payloadLength
            > WebsiteTrackingPipeNames
                .MaximumMessageBytes
        )
        {
            throw new InvalidDataException(
                "Website Tracking framed payload length is invalid."
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

        return payload;
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
            int read =
                await stream.ReadAsync(
                    buffer.AsMemory(
                        offset,
                        buffer.Length
                        - offset
                    ),
                    cancellationToken
                );

            if (
                read == 0
            )
            {
                throw new EndOfStreamException(
                    "Website Tracking pipe closed before the complete frame was received."
                );
            }

            offset +=
                read;
        }
    }
}