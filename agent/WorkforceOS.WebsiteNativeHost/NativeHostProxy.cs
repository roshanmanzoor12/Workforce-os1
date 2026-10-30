using System.Diagnostics;

namespace WorkforceOS.WebsiteNativeHost;

public static class NativeHostProxy
{
    public static async Task<int> RunAsync(
        string agentExecutable,
        CancellationToken cancellationToken
    )
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(
            agentExecutable
        );

        if (
            !File.Exists(
                agentExecutable
            )
        )
        {
            return 2;
        }

        ProcessStartInfo startInfo =
            new()
            {
                FileName =
                    agentExecutable,

                Arguments =
                    "--website-tracking-native-host",

                UseShellExecute =
                    false,

                CreateNoWindow =
                    true,

                RedirectStandardInput =
                    true,

                RedirectStandardOutput =
                    true,

                RedirectStandardError =
                    true,
            };

        using Process process =
            new()
            {
                StartInfo =
                    startInfo,

                EnableRaisingEvents =
                    true,
            };

        if (
            !process.Start()
        )
        {
            return 3;
        }

        Stream browserInput =
            Console.OpenStandardInput();

        Stream browserOutput =
            Console.OpenStandardOutput();

        Stream agentInput =
            process
                .StandardInput
                .BaseStream;

        Stream agentOutput =
            process
                .StandardOutput
                .BaseStream;

        Task browserToAgent =
            CopyUntilClosedAsync(
                browserInput,
                agentInput,
                cancellationToken
            );

        Task agentToBrowser =
            CopyUntilClosedAsync(
                agentOutput,
                browserOutput,
                cancellationToken
            );

        Task consumeError =
            ConsumeErrorAsync(
                process,
                cancellationToken
            );

        Task processExit =
            process.WaitForExitAsync(
                cancellationToken
            );

        await Task.WhenAny(
            processExit,
            browserToAgent,
            agentToBrowser
        );

        try
        {
            await agentInput.FlushAsync(
                cancellationToken
            );
        }
        catch
        {
        }

        try
        {
            process.StandardInput.Close();
        }
        catch
        {
        }

        if (
            !process.HasExited
        )
        {
            await processExit;
        }

        await IgnoreFailureAsync(
            browserToAgent
        );

        await IgnoreFailureAsync(
            agentToBrowser
        );

        await IgnoreFailureAsync(
            consumeError
        );

        return process.ExitCode;
    }

    private static async Task
        CopyUntilClosedAsync(
            Stream source,
            Stream destination,
            CancellationToken cancellationToken
        )
    {
        byte[] buffer =
            new byte[
                16 * 1024
            ];

        while (
            !cancellationToken
                .IsCancellationRequested
        )
        {
            int read =
                await source.ReadAsync(
                    buffer.AsMemory(
                        0,
                        buffer.Length
                    ),
                    cancellationToken
                );

            if (
                read == 0
            )
            {
                break;
            }

            await destination.WriteAsync(
                buffer.AsMemory(
                    0,
                    read
                ),
                cancellationToken
            );

            await destination.FlushAsync(
                cancellationToken
            );
        }
    }

    private static async Task
        ConsumeErrorAsync(
            Process process,
            CancellationToken cancellationToken
        )
    {
        char[] buffer =
            new char[
                2048
            ];

        while (
            !cancellationToken
                .IsCancellationRequested
        )
        {
            int read =
                await process
                    .StandardError
                    .ReadAsync(
                        buffer.AsMemory(
                            0,
                            buffer.Length
                        ),
                        cancellationToken
                    );

            if (
                read == 0
            )
            {
                break;
            }

            /*
             * Intentionally discard child stderr here.
             * Do not contaminate Native Messaging stdout.
             */
        }
    }

    private static async Task
        IgnoreFailureAsync(
            Task task
        )
    {
        try
        {
            await task;
        }
        catch
        {
        }
    }
}