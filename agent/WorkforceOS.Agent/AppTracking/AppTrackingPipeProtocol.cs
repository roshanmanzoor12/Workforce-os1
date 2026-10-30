using System.Buffers.Binary;
using System.Text.Json;

namespace WorkforceOS.Agent.AppTracking;

public static class AppTrackingPipeProtocol
{
    private static readonly JsonSerializerOptions JsonOptions =
        new(JsonSerializerDefaults.Web);

    public static async Task WriteAsync(
        Stream stream,
        AppTrackingSessionObservation observation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(
            stream);

        ArgumentNullException.ThrowIfNull(
            observation);

        observation.Validate();

        byte[] payload =
            JsonSerializer.SerializeToUtf8Bytes(
                observation,
                JsonOptions);

        if (
            payload.Length <= 0
            || payload.Length
            > AppTrackingPipeNames.MaximumMessageBytes)
        {
            throw new InvalidOperationException(
                "AppTracking IPC payload size is invalid.");
        }

        byte[] lengthBuffer =
            new byte[sizeof(int)];

        BinaryPrimitives.WriteInt32LittleEndian(
            lengthBuffer,
            payload.Length);

        await stream.WriteAsync(
            lengthBuffer,
            cancellationToken);

        await stream.WriteAsync(
            payload,
            cancellationToken);

        await stream.FlushAsync(
            cancellationToken);
    }

    public static async Task<AppTrackingSessionObservation> ReadAsync(
        Stream stream,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(
            stream);

        byte[] lengthBuffer =
            new byte[sizeof(int)];

        await ReadExactlyAsync(
            stream,
            lengthBuffer,
            cancellationToken);

        int payloadLength =
            BinaryPrimitives.ReadInt32LittleEndian(
                lengthBuffer);

        if (
            payloadLength <= 0
            || payloadLength
            > AppTrackingPipeNames.MaximumMessageBytes)
        {
            throw new InvalidDataException(
                $"Invalid AppTracking IPC message length: {payloadLength}.");
        }

        byte[] payload =
            new byte[payloadLength];

        await ReadExactlyAsync(
            stream,
            payload,
            cancellationToken);

        AppTrackingSessionObservation? observation =
            JsonSerializer.Deserialize<AppTrackingSessionObservation>(
                payload,
                JsonOptions);

        if (observation is null)
        {
            throw new InvalidDataException(
                "Unable to deserialize AppTracking IPC observation.");
        }

        observation.Validate();

        return observation;
    }

    private static async Task ReadExactlyAsync(
        Stream stream,
        Memory<byte> buffer,
        CancellationToken cancellationToken)
    {
        int offset =
            0;

        while (offset < buffer.Length)
        {
            int read =
                await stream.ReadAsync(
                    buffer[offset..],
                    cancellationToken);

            if (read == 0)
            {
                throw new EndOfStreamException(
                    "AppTracking IPC stream ended before the complete message was received.");
            }

            offset += read;
        }
    }
}