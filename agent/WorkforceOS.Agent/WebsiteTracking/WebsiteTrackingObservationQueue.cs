using System.Threading.Channels;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingObservationQueue
{
    private const int Capacity =
        256;

    private readonly
        Channel<
            WebsiteTrackingObservation
        >
        _channel;

    public WebsiteTrackingObservationQueue()
    {
        BoundedChannelOptions options =
            new(
                Capacity
            )
            {
                FullMode =
                    BoundedChannelFullMode
                        .DropOldest,

                SingleReader =
                    true,

                SingleWriter =
                    false,

                AllowSynchronousContinuations =
                    false,
            };

        _channel =
            Channel.CreateBounded<
                WebsiteTrackingObservation
            >(
                options
            );
    }

    public bool TryWrite(
        WebsiteTrackingObservation observation
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        return _channel
            .Writer
            .TryWrite(
                observation
            );
    }

    public ValueTask<
        WebsiteTrackingObservation
    > ReadAsync(
        CancellationToken cancellationToken
    )
    {
        return _channel
            .Reader
            .ReadAsync(
                cancellationToken
            );
    }

    public IAsyncEnumerable<
        WebsiteTrackingObservation
    > ReadAllAsync(
        CancellationToken cancellationToken
    )
    {
        return _channel
            .Reader
            .ReadAllAsync(
                cancellationToken
            );
    }
}