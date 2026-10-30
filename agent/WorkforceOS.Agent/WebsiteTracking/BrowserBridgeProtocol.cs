using System.Buffers.Binary;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.WebsiteTracking;

public static class BrowserBridgeProtocol
{
    private const int NativeHeaderBytes =
        4;

    private static readonly
        JsonSerializerOptions
        SerializerOptions =
            new()
            {
                PropertyNamingPolicy =
                    JsonNamingPolicy.CamelCase,

                PropertyNameCaseInsensitive =
                    true,

                DefaultIgnoreCondition =
                    JsonIgnoreCondition
                        .WhenWritingNull,
            };

    public static async Task<
        BrowserBridgeMessage?
    > ReadNativeMessageAsync(
        Stream input,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            input
        );

        byte[] header =
            new byte[
                NativeHeaderBytes
            ];

        int headerRead =
            await ReadExactAsync(
                input,
                header,
                cancellationToken
            );

        if (headerRead == 0)
        {
            return null;
        }

        if (
            headerRead
            != NativeHeaderBytes
        )
        {
            throw new InvalidDataException(
                "Incomplete native messaging header."
            );
        }

        int payloadLength =
            BinaryPrimitives
                .ReadInt32LittleEndian(
                    header
                );

        if (
            payloadLength <= 0
            || payloadLength
            > WebsiteTrackingPipeNames
                .MaximumMessageBytes
        )
        {
            throw new InvalidDataException(
                "Invalid native messaging payload size."
            );
        }

        byte[] payload =
            new byte[
                payloadLength
            ];

        int payloadRead =
            await ReadExactAsync(
                input,
                payload,
                cancellationToken
            );

        if (
            payloadRead
            != payloadLength
        )
        {
            throw new InvalidDataException(
                "Incomplete native messaging payload."
            );
        }

        BrowserBridgeMessage?
            message =
                JsonSerializer.Deserialize<
                    BrowserBridgeMessage
                >(
                    payload,
                    SerializerOptions
                );

        if (
            message is null
        )
        {
            throw new InvalidDataException(
                "Invalid browser bridge message."
            );
        }

        return message;
    }

    public static async Task WriteNativeMessageAsync(
        Stream output,
        object payload,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            output
        );

        ArgumentNullException.ThrowIfNull(
            payload
        );

        byte[] body =
            JsonSerializer.SerializeToUtf8Bytes(
                payload,
                SerializerOptions
            );

        if (
            body.Length
            > WebsiteTrackingPipeNames
                .MaximumMessageBytes
        )
        {
            throw new InvalidDataException(
                "Native messaging response exceeds maximum size."
            );
        }

        byte[] header =
            new byte[
                NativeHeaderBytes
            ];

        BinaryPrimitives
            .WriteInt32LittleEndian(
                header,
                body.Length
            );

        await output.WriteAsync(
            header,
            cancellationToken
        );

        await output.WriteAsync(
            body,
            cancellationToken
        );

        await output.FlushAsync(
            cancellationToken
        );
    }

    private static async Task<int>
        ReadExactAsync(
            Stream input,
            byte[] buffer,
            CancellationToken cancellationToken
        )
    {
        int totalRead =
            0;

        while (
            totalRead
            < buffer.Length
        )
        {
            int read =
                await input.ReadAsync(
                    buffer.AsMemory(
                        totalRead,
                        buffer.Length
                        - totalRead
                    ),
                    cancellationToken
                );

            if (
                read == 0
            )
            {
                break;
            }

            totalRead +=
                read;
        }

        return totalRead;
    }
}