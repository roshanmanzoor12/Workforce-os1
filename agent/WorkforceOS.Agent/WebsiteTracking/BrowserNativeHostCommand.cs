using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class BrowserNativeHostCommand
{
    private readonly
        BrowserBridgeValidator
        _validator;

    private readonly
        WebsiteTrackingObservationValidator
        _observationValidator;

    private readonly
        WebsiteTrackingPipeClient
        _pipeClient;

    private readonly
        ILogger<
            BrowserNativeHostCommand
        >
        _logger;

    public BrowserNativeHostCommand(
        BrowserBridgeValidator validator,
        WebsiteTrackingObservationValidator observationValidator,
        WebsiteTrackingPipeClient pipeClient,
        ILogger<
            BrowserNativeHostCommand
        > logger
    )
    {
        _validator =
            validator;

        _observationValidator =
            observationValidator;

        _pipeClient =
            pipeClient;

        _logger =
            logger;
    }

    public async Task<int> RunAsync(
        CancellationToken cancellationToken
    )
    {
        Stream input =
            Console.OpenStandardInput();

        Stream output =
            Console.OpenStandardOutput();

        while (
            !cancellationToken
                .IsCancellationRequested
        )
        {
            BrowserBridgeMessage? message =
                await BrowserBridgeProtocol
                    .ReadNativeMessageAsync(
                        input,
                        cancellationToken
                    );

            if (
                message is null
            )
            {
                break;
            }

            if (
                !_validator.TryConvert(
                    message,
                    out WebsiteTrackingObservation observation,
                    out string? bridgeError
                )
            )
            {
                await WriteResponseAsync(
                    output,
                    false,
                    bridgeError,
                    cancellationToken
                );

                continue;
            }

            if (
                !_observationValidator
                    .TryValidateAndNormalize(
                        observation,
                        out WebsiteTrackingObservation normalized,
                        out string? validationError
                    )
            )
            {
                await WriteResponseAsync(
                    output,
                    false,
                    validationError,
                    cancellationToken
                );

                continue;
            }

            try
            {
                WebsiteTrackingPipeAck ack =
                    await _pipeClient.SendAsync(
                        normalized,
                        cancellationToken
                    );

                await WriteResponseAsync(
                    output,
                    ack.Accepted,
                    ack.Error,
                    cancellationToken
                );
            }
            catch (
                WebsiteTrackingPipeConnectionException exception
            )
            {
                string error =
                    "Agent pipe failure; "
                    + $"attempts={exception.Attempts}; "
                    + $"type={exception.LastExceptionType ?? "unknown"}; "
                    + $"hresult={FormatHResult(exception.LastHResult)}";

                await WriteResponseAsync(
                    output,
                    false,
                    error,
                    cancellationToken
                );
            }
            catch (
                Exception exception
            )
            {
                _logger.LogWarning(
                    exception,
                    "Website observation native-host forwarding failed."
                );

                await WriteResponseAsync(
                    output,
                    false,
                    (
                        "Agent service failure; "
                        + exception
                            .GetType()
                            .Name
                    ),
                    cancellationToken
                );
            }
        }

        return 0;
    }

    private static async Task WriteResponseAsync(
        Stream output,
        bool accepted,
        string? error,
        CancellationToken cancellationToken
    )
    {
        await BrowserBridgeProtocol
            .WriteNativeMessageAsync(
                output,
                new
                {
                    accepted,
                    error,
                },
                cancellationToken
            );
    }

    private static string FormatHResult(
        int? value
    )
    {
        if (
            value is null
        )
        {
            return "unknown";
        }

        return (
            "0x"
            + unchecked(
                (uint)value.Value
            ).ToString(
                "X8"
            )
        );
    }
}